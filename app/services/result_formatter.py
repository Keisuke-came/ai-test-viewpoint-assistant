from app.domain.models import LlmResult, DisplayResult
from app.utils.category_utils import group_by_category
from app.services.markdown_formatter import build_markdown_text


def to_display_result(llm_result: LlmResult) -> DisplayResult:
    grouped = group_by_category(llm_result.viewpoints)
    markdown = build_markdown_text(llm_result)
    return DisplayResult(
        summary=llm_result.summary,
        grouped_viewpoints=grouped,
        ambiguities=llm_result.ambiguities,
        notes=llm_result.notes,
        markdown_text=markdown,
    )
