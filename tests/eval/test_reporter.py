"""app/eval/reporter.py のテスト。

JSON / Markdown 生成を検証する。
"""
import json
import pytest

from app.eval.models import CaseEvalResult, EvalReport
from app.eval.reporter import to_json, to_markdown


# ──────────────────────────────────────────────
# フィクスチャ
# ──────────────────────────────────────────────

@pytest.fixture
def all_pass_report() -> EvalReport:
    return EvalReport(
        total=2,
        passed=2,
        failed=0,
        results=[
            CaseEvalResult(
                case_id="TC-001",
                title="ログイン画面",
                passed=True,
                failures=[],
                viewpoint_count=6,
                categories=["正常系", "異常系", "境界値"],
                cache_hit=False,
                duration_seconds=1.23,
                token_usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            ),
            CaseEvalResult(
                case_id="TC-002",
                title="登録 API",
                passed=True,
                failures=[],
                viewpoint_count=5,
                categories=["正常系", "異常系"],
                cache_hit=True,
                duration_seconds=0.01,
                token_usage=None,
            ),
        ],
        total_duration_seconds=1.24,
        total_tokens=300,
    )


@pytest.fixture
def with_failure_report() -> EvalReport:
    return EvalReport(
        total=2,
        passed=1,
        failed=1,
        results=[
            CaseEvalResult(
                case_id="TC-001",
                title="ログイン画面",
                passed=True,
                failures=[],
                viewpoint_count=6,
                categories=["正常系", "異常系"],
                cache_hit=False,
                duration_seconds=1.0,
                token_usage=None,
            ),
            CaseEvalResult(
                case_id="TC-002",
                title="失敗ケース",
                passed=False,
                failures=["観点数不足: 2 < 5", "期待カテゴリ(all)欠落: '境界値'"],
                viewpoint_count=2,
                categories=["正常系"],
                cache_hit=False,
                duration_seconds=2.0,
                token_usage=None,
            ),
        ],
        total_duration_seconds=3.0,
        total_tokens=None,
    )


# ──────────────────────────────────────────────
# to_json のテスト
# ──────────────────────────────────────────────

def test_to_json_valid_structure(all_pass_report: EvalReport) -> None:
    """to_json が有効な JSON を返す。"""
    result = to_json(all_pass_report)
    data = json.loads(result)

    assert "generated_at" in data
    assert "summary" in data
    assert "results" in data


def test_to_json_summary_fields(all_pass_report: EvalReport) -> None:
    """to_json の summary セクションに必須フィールドが含まれる。"""
    data = json.loads(to_json(all_pass_report))
    summary = data["summary"]

    assert summary["total"] == 2
    assert summary["passed"] == 2
    assert summary["failed"] == 0
    assert summary["pass_rate"] == "100.0%"
    assert summary["total_tokens"] == 300


def test_to_json_results_count(all_pass_report: EvalReport) -> None:
    """to_json の results に全ケースが含まれる。"""
    data = json.loads(to_json(all_pass_report))
    assert len(data["results"]) == 2


def test_to_json_case_fields(all_pass_report: EvalReport) -> None:
    """to_json の各ケースに必須フィールドが含まれる。"""
    data = json.loads(to_json(all_pass_report))
    case = data["results"][0]

    assert case["case_id"] == "TC-001"
    assert case["passed"] is True
    assert case["failures"] == []
    assert case["viewpoint_count"] == 6
    assert case["cache_hit"] is False


def test_to_json_with_failures(with_failure_report: EvalReport) -> None:
    """FAIL ケースの failures フィールドに失敗理由が含まれる。"""
    data = json.loads(to_json(with_failure_report))
    failed_case = next(r for r in data["results"] if not r["passed"])

    assert len(failed_case["failures"]) == 2
    assert any("観点数不足" in f for f in failed_case["failures"])


def test_to_json_pass_rate_calculation(with_failure_report: EvalReport) -> None:
    """合格率が正しく計算される。"""
    data = json.loads(to_json(with_failure_report))
    assert data["summary"]["pass_rate"] == "50.0%"


def test_to_json_empty_report() -> None:
    """ケース数 0 の EvalReport でも to_json が動作する。"""
    report = EvalReport(total=0, passed=0, failed=0, results=[], total_duration_seconds=0.0)
    data = json.loads(to_json(report))
    assert data["summary"]["pass_rate"] == "N/A"
    assert data["results"] == []


# ──────────────────────────────────────────────
# to_markdown のテスト
# ──────────────────────────────────────────────

def test_to_markdown_contains_header(all_pass_report: EvalReport) -> None:
    """Markdown にレポートタイトルが含まれる。"""
    md = to_markdown(all_pass_report)
    assert "# テスト観点生成 評価レポート" in md


def test_to_markdown_contains_summary_table(all_pass_report: EvalReport) -> None:
    """Markdown にサマリテーブルが含まれる。"""
    md = to_markdown(all_pass_report)
    assert "実行ケース数" in md
    assert "PASS" in md
    assert "合格率" in md


def test_to_markdown_contains_case_table(all_pass_report: EvalReport) -> None:
    """Markdown にケース別結果テーブルが含まれる。"""
    md = to_markdown(all_pass_report)
    assert "TC-001" in md
    assert "TC-002" in md
    assert "✅ PASS" in md


def test_to_markdown_fail_detail_section(with_failure_report: EvalReport) -> None:
    """FAIL があれば失敗ケース詳細セクションが含まれる。"""
    md = to_markdown(with_failure_report)
    assert "## 失敗ケース詳細" in md
    assert "観点数不足" in md


def test_to_markdown_no_fail_detail_section(all_pass_report: EvalReport) -> None:
    """全 PASS なら失敗ケース詳細セクションが含まれない。"""
    md = to_markdown(all_pass_report)
    assert "## 失敗ケース詳細" not in md


def test_to_markdown_cache_hit_shown(all_pass_report: EvalReport) -> None:
    """キャッシュヒット/ミスが Markdown に表示される。"""
    md = to_markdown(all_pass_report)
    assert "hit" in md
    assert "miss" in md
