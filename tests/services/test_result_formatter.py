import pytest
from app.domain.models import DisplayResult, LlmResult, Viewpoint
from app.services.result_formatter import to_display_result


class TestToDisplayResult:
    def test_returns_display_result(self, sample_llm_result):
        result = to_display_result(sample_llm_result)
        assert isinstance(result, DisplayResult)

    def test_summary_passed_through(self, sample_llm_result):
        result = to_display_result(sample_llm_result)
        assert result.summary == sample_llm_result.summary

    def test_ambiguities_passed_through(self, sample_llm_result):
        result = to_display_result(sample_llm_result)
        assert result.ambiguities == sample_llm_result.ambiguities

    def test_notes_passed_through(self, sample_llm_result):
        result = to_display_result(sample_llm_result)
        assert result.notes == sample_llm_result.notes

    def test_grouped_viewpoints_is_dict(self, sample_llm_result):
        result = to_display_result(sample_llm_result)
        assert isinstance(result.grouped_viewpoints, dict)

    def test_grouped_viewpoints_keys_are_categories(self, sample_llm_result):
        result = to_display_result(sample_llm_result)
        # sample_llm_result には 正常系・異常系・境界値 が含まれる
        assert "正常系" in result.grouped_viewpoints
        assert "異常系" in result.grouped_viewpoints
        assert "境界値" in result.grouped_viewpoints

    def test_all_viewpoints_present_in_grouped(self, sample_llm_result):
        result = to_display_result(sample_llm_result)
        total = sum(len(vps) for vps in result.grouped_viewpoints.values())
        assert total == len(sample_llm_result.viewpoints)

    def test_markdown_text_not_empty(self, sample_llm_result):
        result = to_display_result(sample_llm_result)
        assert isinstance(result.markdown_text, str)
        assert len(result.markdown_text) > 0

    def test_markdown_text_contains_summary(self, sample_llm_result):
        result = to_display_result(sample_llm_result)
        assert sample_llm_result.summary in result.markdown_text

    def test_empty_viewpoints(self):
        llm_result = LlmResult(
            summary="サマリ",
            viewpoints=[],
            ambiguities=[],
            notes=[],
        )
        result = to_display_result(llm_result)
        assert result.grouped_viewpoints == {}
        assert result.summary == "サマリ"

    def test_unknown_category_normalized_to_sonota(self):
        llm_result = LlmResult(
            summary="s",
            viewpoints=[
                Viewpoint(
                    category="未知カテゴリXYZ",
                    title="タイトル",
                    description="d",
                    priority="中",
                )
            ],
            ambiguities=[],
            notes=[],
        )
        result = to_display_result(llm_result)
        assert "その他" in result.grouped_viewpoints
        assert "未知カテゴリXYZ" not in result.grouped_viewpoints
