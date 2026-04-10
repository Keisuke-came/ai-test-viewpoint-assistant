from app.domain.models import LlmResult
from app.utils.category_utils import group_by_category


def build_markdown_text(llm_result: LlmResult) -> str:
    lines: list[str] = []

    lines.append("# サマリ")
    lines.append(llm_result.summary)
    lines.append("")

    lines.append("# テスト観点")
    grouped = group_by_category(llm_result.viewpoints)
    for category, viewpoints in grouped.items():
        lines.append(f"## {category}")
        for vp in viewpoints:
            lines.append(f"- [{vp.priority}] {vp.title}")
            lines.append(f"  - {vp.description}")
        lines.append("")

    if llm_result.ambiguities:
        lines.append("# 曖昧点・確認事項")
        for item in llm_result.ambiguities:
            lines.append(f"- {item}")
        lines.append("")

    if llm_result.notes:
        lines.append("# 注意事項")
        for item in llm_result.notes:
            lines.append(f"- {item}")
        lines.append("")

    return "\n".join(lines)
