"""app/eval/runner.py のテスト。

キャッシュヒット/ミス、LLM エラー時の挙動、EvalReport 集計値を検証する。
"""
import pytest
from pathlib import Path
from typing import Dict, Optional
from unittest.mock import MagicMock, patch

from app.domain.models import LlmApiError, LlmResult, ResponseFormatError, Viewpoint
from app.eval import cache as eval_cache
from app.eval.models import EvalCase, Expectations
from app.eval.runner import run_cases, _run_single


# ──────────────────────────────────────────────
# フィクスチャ
# ──────────────────────────────────────────────

@pytest.fixture(autouse=True)
def tmp_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """全テストで一時キャッシュディレクトリを使用する。"""
    monkeypatch.setattr(eval_cache, "CACHE_DIR", tmp_path / ".eval_cache_test")


@pytest.fixture
def sample_llm_result() -> LlmResult:
    return LlmResult(
        summary="テストサマリ",
        viewpoints=[
            Viewpoint(category="正常系", title="正常テスト", description="成功する", priority="高"),
            Viewpoint(category="異常系", title="異常テスト", description="失敗する", priority="高"),
        ],
        ambiguities=[],
        notes=[],
    )


@pytest.fixture
def valid_case() -> EvalCase:
    return EvalCase(
        case_id="TC-001",
        title="テストケース",
        target_type="screen",
        spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
        supplemental_text="",
        expectations=Expectations(min_viewpoints=2),
    )


def _make_mock_client(
    llm_result: LlmResult,
    token_usage: Optional[Dict] = None,
) -> MagicMock:
    """LlmResult を返すモッククライアントを生成する。

    generate_viewpoints を呼ぶと client.last_usage を設定し、
    実際の OpenAiClient に近い挙動をシミュレートする。
    """
    client = MagicMock()
    client.last_usage = None

    def _side_effect(*args, **kwargs):
        client.last_usage = token_usage
        return llm_result.model_dump_json()

    client.generate_viewpoints.side_effect = _side_effect
    return client


# ──────────────────────────────────────────────
# キャッシュヒット: LLM を呼ばない
# ──────────────────────────────────────────────

def test_cache_hit_skips_llm(
    valid_case: EvalCase, sample_llm_result: LlmResult
) -> None:
    """キャッシュが存在する場合、LLM を呼び出さない。"""
    eval_cache.save(
        valid_case.target_type,
        valid_case.spec_text,
        valid_case.supplemental_text,
        sample_llm_result,
    )
    mock_client = _make_mock_client(sample_llm_result)

    result = _run_single(valid_case, refresh=False, client=mock_client)

    assert result.cache_hit is True
    mock_client.generate_viewpoints.assert_not_called()


def test_cache_hit_result_has_correct_data(
    valid_case: EvalCase, sample_llm_result: LlmResult
) -> None:
    """キャッシュヒット時の CaseEvalResult が正しい値を持つ。"""
    eval_cache.save(
        valid_case.target_type,
        valid_case.spec_text,
        valid_case.supplemental_text,
        sample_llm_result,
    )
    mock_client = _make_mock_client(sample_llm_result)

    result = _run_single(valid_case, refresh=False, client=mock_client)

    assert result.case_id == "TC-001"
    assert result.viewpoint_count == 2
    assert result.token_usage is None  # キャッシュヒット時はトークン情報なし


# ──────────────────────────────────────────────
# キャッシュミス: LLM を呼ぶ
# ──────────────────────────────────────────────

def test_cache_miss_calls_llm(
    valid_case: EvalCase, sample_llm_result: LlmResult
) -> None:
    """キャッシュが存在しない場合、LLM を呼び出す。"""
    mock_client = _make_mock_client(sample_llm_result)

    result = _run_single(valid_case, refresh=False, client=mock_client)

    assert result.cache_hit is False
    mock_client.generate_viewpoints.assert_called_once()


def test_refresh_ignores_cache(
    valid_case: EvalCase, sample_llm_result: LlmResult
) -> None:
    """refresh=True の場合、キャッシュが存在しても LLM を再呼び出しする。"""
    eval_cache.save(
        valid_case.target_type,
        valid_case.spec_text,
        valid_case.supplemental_text,
        sample_llm_result,
    )
    mock_client = _make_mock_client(sample_llm_result)

    result = _run_single(valid_case, refresh=True, client=mock_client)

    assert result.cache_hit is False
    mock_client.generate_viewpoints.assert_called_once()


# ──────────────────────────────────────────────
# LLM エラー時: FAIL として記録し例外を伝播させない
# ──────────────────────────────────────────────

def test_llm_api_error_returns_fail_result(valid_case: EvalCase) -> None:
    """LlmApiError が発生しても run_single は例外を raise せず FAIL を返す。"""
    mock_client = MagicMock()
    mock_client.last_usage = None
    mock_client.generate_viewpoints.side_effect = LlmApiError("API エラー")

    result = _run_single(valid_case, refresh=False, client=mock_client)

    assert result.passed is False
    assert any("LLM エラー" in f for f in result.failures)
    assert result.viewpoint_count == 0


def test_response_format_error_returns_fail_result(valid_case: EvalCase) -> None:
    """ResponseFormatError が発生しても run_single は例外を raise せず FAIL を返す。"""
    mock_client = MagicMock()
    mock_client.last_usage = None
    mock_client.generate_viewpoints.return_value = "invalid json!!!"

    result = _run_single(valid_case, refresh=False, client=mock_client)

    assert result.passed is False
    assert any("LLM エラー" in f for f in result.failures)


def test_one_error_does_not_stop_other_cases(sample_llm_result: LlmResult) -> None:
    """1件が LLM エラーでも、残りのケースは実行される。"""
    cases = [
        EvalCase(
            case_id="TC-001",
            title="失敗ケース",
            target_type="screen",
            spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
            supplemental_text="",
        ),
        EvalCase(
            case_id="TC-002",
            title="成功ケース",
            target_type="api",
            spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
            supplemental_text="",
        ),
    ]

    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise LlmApiError("1件目のエラー")
        return sample_llm_result.model_dump_json()

    mock_client = MagicMock()
    mock_client.last_usage = None
    mock_client.generate_viewpoints.side_effect = side_effect

    report = run_cases(cases, refresh=False, client=mock_client)

    assert report.total == 2
    assert report.failed == 1
    assert report.passed == 1


# ──────────────────────────────────────────────
# EvalReport 集計値
# ──────────────────────────────────────────────

def test_report_aggregation(sample_llm_result: LlmResult) -> None:
    """run_cases の EvalReport が passed/failed/total を正しく集計する。"""
    # spec_text を変えてキャッシュキーが異なる 3 ケースにする
    specs = [
        "ユーザーがメールアドレスとパスワードを入力してログインする機能",
        "ユーザーが新規登録するための情報を入力するAPI仕様です。",
        "管理者がCSVで月次レポートを出力するバッチ処理の仕様です。",
    ]
    cases = [
        EvalCase(
            case_id=f"TC-00{i}",
            title=f"ケース {i}",
            target_type="screen",
            spec_text=spec,
            supplemental_text="",
            expectations=Expectations(min_viewpoints=1),
        )
        for i, spec in enumerate(specs)
    ]
    token_usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    mock_client = _make_mock_client(sample_llm_result, token_usage=token_usage)

    report = run_cases(cases, refresh=False, client=mock_client)

    assert report.total == 3
    assert report.passed == 3
    assert report.failed == 0
    assert report.total_tokens == 450  # 150 * 3（全ケースがキャッシュミスのため）


def test_report_total_tokens_none_on_missing_usage(valid_case: EvalCase) -> None:
    """トークン情報が取得できない場合（token_usage=None）、total_tokens は None になる。"""
    result_data = LlmResult(
        summary="s",
        viewpoints=[Viewpoint(category="正常系", title="t", description="d", priority="高")],
        ambiguities=[],
        notes=[],
    )
    # token_usage=None でモック作成（トークン情報なし）
    mock_client = _make_mock_client(result_data, token_usage=None)

    report = run_cases([valid_case], refresh=False, client=mock_client)

    assert report.total_tokens is None


# ──────────────────────────────────────────────
# 不正な target_type
# ──────────────────────────────────────────────

def test_invalid_target_type_returns_fail(sample_llm_result: LlmResult) -> None:
    """不正な target_type を持つケースは FAIL として記録される。"""
    case = EvalCase(
        case_id="TC-BAD",
        title="不正種別",
        target_type="invalid_type",
        spec_text="仕様テキストサンプル",
        supplemental_text="",
    )
    mock_client = _make_mock_client(sample_llm_result)

    result = _run_single(case, refresh=False, client=mock_client)

    assert result.passed is False
    assert any("不正な target_type" in f for f in result.failures)
    mock_client.generate_viewpoints.assert_not_called()
