"""評価ランナー。複数の評価ケースを実行してレポートを生成する。

キャッシュが存在する場合は LLM を再呼び出しせず再利用する（トークン節約）。
refresh=True を指定するとキャッシュを無視して再生成する。

LLM 呼び出しがエラーになった場合は、そのケースを FAIL として記録し、
残りのケースを継続実行する（1件のエラーで全体が止まらない）。
"""
import logging
import time
from typing import List, Optional

from app.domain.models import InputData, LlmApiError, LlmResult, ResponseFormatError
from app.eval import cache as eval_cache
from app.eval.evaluator import evaluate
from app.eval.models import CaseEvalResult, EvalCase, EvalReport
from app.llm.openai_client import OpenAiClient
from app.llm.schemas import parse_llm_result
from app.services.prompt_builder import build_system_prompt, build_user_prompt

logger = logging.getLogger(__name__)

_VALID_TARGET_TYPES = {"screen", "api", "batch", "ticket", "other"}


def run_cases(
    cases: List[EvalCase],
    refresh: bool = False,
    client: Optional[OpenAiClient] = None,
) -> EvalReport:
    """複数の評価ケースを実行してレポートを生成する。

    Args:
        cases: EvalCase のリスト。
        refresh: True の場合はキャッシュを無視して LLM を再実行する。
        client: テスト用 OpenAiClient（省略時は自動生成）。

    Returns:
        EvalReport。
    """
    _client = client or OpenAiClient()
    results: List[CaseEvalResult] = []
    total_start = time.monotonic()
    accumulated_tokens: int = 0
    tokens_available: bool = True

    for case in cases:
        result = _run_single(case, refresh, _client)
        results.append(result)
        if result.token_usage is not None:
            accumulated_tokens += result.token_usage.get("total_tokens", 0)
        elif not result.cache_hit:
            # キャッシュミスなのにトークン情報がない場合は合計を不明とする
            tokens_available = False

    total_duration = round(time.monotonic() - total_start, 2)
    passed = sum(1 for r in results if r.passed)

    return EvalReport(
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
        total_duration_seconds=total_duration,
        total_tokens=accumulated_tokens if tokens_available else None,
    )


def _run_single(case: EvalCase, refresh: bool, client: OpenAiClient) -> CaseEvalResult:
    """1 ケースを実行して評価結果を返す。

    LLM 呼び出しやパースで例外が発生した場合は、
    失敗理由を failures に詰めた CaseEvalResult を返す（例外を外に伝播させない）。
    """
    start = time.monotonic()

    llm_result: Optional[LlmResult] = None
    if not refresh:
        llm_result = eval_cache.get(case.target_type, case.spec_text, case.supplemental_text)

    if llm_result is not None:
        duration = round(time.monotonic() - start, 2)
        logger.debug("キャッシュヒット: %s", case.case_id)
        failures = evaluate(llm_result, case.expectations)
        categories = sorted(set(vp.category for vp in llm_result.viewpoints))
        return CaseEvalResult(
            case_id=case.case_id,
            title=case.title,
            passed=len(failures) == 0,
            failures=failures,
            viewpoint_count=len(llm_result.viewpoints),
            categories=categories,
            cache_hit=True,
            duration_seconds=duration,
            token_usage=None,
        )

    # キャッシュミス: LLM を呼び出す
    if case.target_type not in _VALID_TARGET_TYPES:
        duration = round(time.monotonic() - start, 2)
        return CaseEvalResult(
            case_id=case.case_id,
            title=case.title,
            passed=False,
            failures=[f"不正な target_type: '{case.target_type}'"],
            viewpoint_count=0,
            categories=[],
            cache_hit=False,
            duration_seconds=duration,
            token_usage=None,
        )

    client.last_usage = None  # 前回の値が混入しないようリセット
    try:
        input_data = InputData(
            target_type=case.target_type,  # type: ignore[arg-type]
            spec_text=case.spec_text,
            supplemental_text=case.supplemental_text,
        )
        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(input_data)
        raw_text = client.generate_viewpoints(system_prompt, user_prompt)
        llm_result = parse_llm_result(raw_text)
    except (LlmApiError, ResponseFormatError) as e:
        duration = round(time.monotonic() - start, 2)
        logger.error("ケース %s の LLM 呼び出しに失敗: %s", case.case_id, e)
        return CaseEvalResult(
            case_id=case.case_id,
            title=case.title,
            passed=False,
            failures=[f"LLM エラー: {e}"],
            viewpoint_count=0,
            categories=[],
            cache_hit=False,
            duration_seconds=duration,
            token_usage=None,
        )

    eval_cache.save(case.target_type, case.spec_text, case.supplemental_text, llm_result)
    token_usage = client.last_usage
    logger.debug("LLM 呼び出し完了: %s (token_usage=%s)", case.case_id, token_usage)

    duration = round(time.monotonic() - start, 2)
    failures = evaluate(llm_result, case.expectations)
    categories = sorted(set(vp.category for vp in llm_result.viewpoints))

    return CaseEvalResult(
        case_id=case.case_id,
        title=case.title,
        passed=len(failures) == 0,
        failures=failures,
        viewpoint_count=len(llm_result.viewpoints),
        categories=categories,
        cache_hit=False,
        duration_seconds=duration,
        token_usage=token_usage,
    )
