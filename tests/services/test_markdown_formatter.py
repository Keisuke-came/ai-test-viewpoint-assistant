import pytest
from app.domain.models import LlmResult, Viewpoint
from app.services.markdown_formatter import build_markdown_text


class TestBuildMarkdownText:
    def test_contains_summary_section(self, sample_llm_result):
        result = build_markdown_text(sample_llm_result)
        assert "# サマリ" in result
        assert sample_llm_result.summary in result

    def test_contains_viewpoints_section(self, sample_llm_result):
        result = build_markdown_text(sample_llm_result)
        assert "# テスト観点" in result

    def test_viewpoint_format_priority_and_title(self, sample_llm_result):
        result = build_markdown_text(sample_llm_result)
        # [高] タイトル の形式
        assert "- [高]" in result

    def test_viewpoint_format_description_indented(self, sample_llm_result):
        result = build_markdown_text(sample_llm_result)
        # description は "  - " で始まる行として出力される
        assert "  - " in result

    def test_category_as_h2(self, sample_llm_result):
        result = build_markdown_text(sample_llm_result)
        assert "## 正常系" in result
        assert "## 異常系" in result
        assert "## 境界値" in result

    def test_ambiguities_section_present_when_not_empty(self, sample_llm_result):
        result = build_markdown_text(sample_llm_result)
        assert "# 曖昧点・確認事項" in result
        for item in sample_llm_result.ambiguities:
            assert f"- {item}" in result

    def test_ambiguities_section_absent_when_empty(self):
        llm_result = LlmResult(
            summary="s",
            viewpoints=[],
            ambiguities=[],
            notes=["注意"],
        )
        result = build_markdown_text(llm_result)
        assert "# 曖昧点・確認事項" not in result

    def test_notes_section_present_when_not_empty(self, sample_llm_result):
        result = build_markdown_text(sample_llm_result)
        assert "# 注意事項" in result
        for item in sample_llm_result.notes:
            assert f"- {item}" in result

    def test_notes_section_absent_when_empty(self):
        llm_result = LlmResult(
            summary="s",
            viewpoints=[],
            ambiguities=["確認事項"],
            notes=[],
        )
        result = build_markdown_text(llm_result)
        assert "# 注意事項" not in result

    def test_empty_viewpoints_no_category_headers(self):
        llm_result = LlmResult(
            summary="サマリ",
            viewpoints=[],
            ambiguities=[],
            notes=[],
        )
        result = build_markdown_text(llm_result)
        assert "# サマリ" in result
        assert "## " not in result

    def test_viewpoints_ordered_by_category_then_priority(self):
        llm_result = LlmResult(
            summary="s",
            viewpoints=[
                Viewpoint(category="異常系", title="B", description="d", priority="高"),
                Viewpoint(category="正常系", title="A", description="d", priority="高"),
            ],
            ambiguities=[],
            notes=[],
        )
        result = build_markdown_text(llm_result)
        pos_normal = result.index("## 正常系")
        pos_error = result.index("## 異常系")
        assert pos_normal < pos_error

    def test_returns_string(self, sample_llm_result):
        result = build_markdown_text(sample_llm_result)
        assert isinstance(result, str)
