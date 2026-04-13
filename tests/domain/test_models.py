import pytest
from pydantic import ValidationError
from app.domain.models import (
    InputData,
    Viewpoint,
    LlmResult,
    DisplayResult,
    InputValidationError,
    LlmApiError,
    ResponseFormatError,
    ApplicationError,
)


class TestInputData:
    def test_valid(self):
        data = InputData(
            target_type="screen",
            spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
        )
        assert data.target_type == "screen"
        assert data.supplemental_text == ""

    @pytest.mark.parametrize("target_type", ["screen", "api", "batch", "ticket", "other"])
    def test_all_valid_target_types(self, target_type):
        data = InputData(
            target_type=target_type,
            spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
        )
        assert data.target_type == target_type

    def test_invalid_target_type(self):
        with pytest.raises(ValidationError):
            InputData(
                target_type="unknown",
                spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
            )

    def test_spec_text_too_short(self):
        with pytest.raises(ValidationError):
            InputData(target_type="screen", spec_text="短すぎる仕様")

    def test_spec_text_exactly_20_chars(self):
        # 境界値: ちょうど20文字
        spec = "あ" * 20
        data = InputData(target_type="api", spec_text=spec)
        assert len(data.spec_text) == 20

    def test_spec_text_19_chars_raises(self):
        with pytest.raises(ValidationError):
            InputData(target_type="api", spec_text="あ" * 19)

    def test_supplemental_text_default_empty(self):
        data = InputData(
            target_type="batch",
            spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
        )
        assert data.supplemental_text == ""


class TestViewpoint:
    @pytest.mark.parametrize("priority", ["高", "中", "低"])
    def test_valid_priority(self, priority):
        vp = Viewpoint(
            category="正常系",
            title="タイトル",
            description="説明",
            priority=priority,
        )
        assert vp.priority == priority

    def test_invalid_priority(self):
        with pytest.raises(ValidationError):
            Viewpoint(
                category="正常系",
                title="タイトル",
                description="説明",
                priority="最高",
            )


class TestLlmResult:
    def test_valid(self, sample_llm_result):
        assert sample_llm_result.summary != ""
        assert isinstance(sample_llm_result.viewpoints, list)
        assert isinstance(sample_llm_result.ambiguities, list)
        assert isinstance(sample_llm_result.notes, list)

    def test_empty_lists_allowed(self):
        result = LlmResult(
            summary="サマリ",
            viewpoints=[],
            ambiguities=[],
            notes=[],
        )
        assert result.viewpoints == []


class TestDisplayResult:
    def test_valid(self, sample_viewpoint):
        result = DisplayResult(
            summary="サマリ",
            grouped_viewpoints={"正常系": [sample_viewpoint]},
            ambiguities=["確認事項"],
            notes=["注意"],
            markdown_text="# サマリ\nサマリ",
        )
        assert result.summary == "サマリ"
        assert "正常系" in result.grouped_viewpoints


class TestCustomExceptions:
    def test_input_validation_error_is_exception(self):
        err = InputValidationError("エラー")
        assert isinstance(err, Exception)
        assert str(err) == "エラー"

    def test_llm_api_error_is_exception(self):
        assert isinstance(LlmApiError("e"), Exception)

    def test_response_format_error_is_exception(self):
        assert isinstance(ResponseFormatError("e"), Exception)

    def test_application_error_is_exception(self):
        assert isinstance(ApplicationError("e"), Exception)
