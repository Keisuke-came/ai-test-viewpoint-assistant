"""評価レポート生成。EvalReport を JSON または Markdown 文字列に変換する純粋関数群。"""
import json
from datetime import datetime
from typing import Dict, List, Optional

from app.eval.models import CaseEvalResult, EvalReport


def to_json(report: EvalReport) -> str:
    """評価レポートを JSON 文字列に変換する。

    Args:
        report: 評価レポート。

    Returns:
        インデント付き JSON 文字列。
    """

    def _result_to_dict(r: CaseEvalResult) -> Dict:
        return {
            "case_id": r.case_id,
            "title": r.title,
            "passed": r.passed,
            "failures": r.failures,
            "viewpoint_count": r.viewpoint_count,
            "categories": r.categories,
            "cache_hit": r.cache_hit,
            "duration_seconds": r.duration_seconds,
            "token_usage": r.token_usage,
        }

    pass_rate = _pass_rate(report)
    data = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "summary": {
            "total": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "pass_rate": pass_rate,
            "total_duration_seconds": report.total_duration_seconds,
            "total_tokens": report.total_tokens,
        },
        "results": [_result_to_dict(r) for r in report.results],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def to_markdown(report: EvalReport) -> str:
    """評価レポートを Markdown 文字列に変換する。

    PR や README に貼りやすい GitHub Flavored Markdown 形式で出力する。

    Args:
        report: 評価レポート。

    Returns:
        Markdown 文字列。
    """
    lines: List[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pass_rate = _pass_rate(report)

    lines.append("# テスト観点生成 評価レポート")
    lines.append(f"_生成日時: {now}_")
    lines.append("")
    lines.append("## サマリ")
    lines.append("")
    lines.append("| 指標 | 値 |")
    lines.append("|---|---|")
    lines.append(f"| 実行ケース数 | {report.total} |")
    lines.append(f"| PASS | {report.passed} |")
    lines.append(f"| FAIL | {report.failed} |")
    lines.append(f"| 合格率 | {pass_rate} |")
    lines.append(f"| 総処理時間 | {report.total_duration_seconds}s |")
    if report.total_tokens is not None:
        lines.append(f"| 総トークン数 | {report.total_tokens:,} |")
    lines.append("")
    lines.append("## ケース別結果")
    lines.append("")
    lines.append("| case_id | タイトル | 判定 | 観点数 | キャッシュ | 時間 | 失敗理由 |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in report.results:
        status = "✅ PASS" if r.passed else "❌ FAIL"
        cache_str = "hit" if r.cache_hit else "miss"
        failures_str = "; ".join(r.failures) if r.failures else "-"
        lines.append(
            f"| {r.case_id} | {r.title} | {status} | {r.viewpoint_count} | {cache_str} | {r.duration_seconds}s | {failures_str} |"
        )
    lines.append("")

    failed = [r for r in report.results if not r.passed]
    if failed:
        lines.append("## 失敗ケース詳細")
        lines.append("")
        for r in failed:
            lines.append(f"### {r.case_id}: {r.title}")
            for f in r.failures:
                lines.append(f"- {f}")
            lines.append("")

    return "\n".join(lines)


def _pass_rate(report: EvalReport) -> str:
    """合格率を文字列で返す。"""
    if report.total == 0:
        return "N/A"
    return f"{report.passed / report.total * 100:.1f}%"
