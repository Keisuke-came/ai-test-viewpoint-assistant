import pytest
from app.domain.models import InputData
from app.services.prompt_builder import build_system_prompt, build_user_prompt


class TestBuildSystemPrompt:
    def test_returns_string(self):
        result = build_system_prompt()
        assert isinstance(result, str)

    def test_contains_json_instruction(self):
        result = build_system_prompt()
        assert "JSON" in result

    def test_contains_qa_role(self):
        result = build_system_prompt()
        assert "QA" in result

    def test_contains_ambiguities_instruction(self):
        result = build_system_prompt()
        assert "ambiguities" in result

    def test_not_empty(self):
        result = build_system_prompt()
        assert len(result) > 0


class TestBuildUserPrompt:
    @pytest.mark.parametrize(
        "target_type, expected_label",
        [
            ("screen", "画面"),
            ("api", "API"),
            ("batch", "バッチ"),
            ("ticket", "チケット"),
            ("other", "その他"),
        ],
    )
    def test_target_type_label_conversion(self, target_type, expected_label):
        data = InputData(
            target_type=target_type,
            spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
        )
        result = build_user_prompt(data)
        assert expected_label in result

    def test_spec_text_is_included(self, valid_input_data):
        result = build_user_prompt(valid_input_data)
        assert valid_input_data.spec_text in result

    def test_supplemental_text_included_when_present(self):
        data = InputData(
            target_type="screen",
            spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
            supplemental_text="ログイン失敗時は3回まで",
        )
        result = build_user_prompt(data)
        assert "ログイン失敗時は3回まで" in result

    def test_supplemental_text_empty_shows_nashi(self):
        data = InputData(
            target_type="api",
            spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
            supplemental_text="",
        )
        result = build_user_prompt(data)
        assert "（なし）" in result

    def test_supplemental_text_whitespace_only_shows_nashi(self):
        data = InputData(
            target_type="api",
            spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
            supplemental_text="   ",
        )
        result = build_user_prompt(data)
        assert "（なし）" in result

    def test_contains_output_requirements(self, valid_input_data):
        result = build_user_prompt(valid_input_data)
        assert "summary" in result
        assert "viewpoints" in result
        assert "ambiguities" in result
        assert "notes" in result

    def test_contains_json_only_instruction(self, valid_input_data):
        result = build_user_prompt(valid_input_data)
        assert "JSONのみ" in result

    def test_unknown_target_type_uses_raw_value(self):
        # TARGET_TYPE_LABELS に存在しない target_type は raw 値がそのまま出力に入る
        # Pydantic のバリデーションを回避するため model_construct() を使用
        data = InputData.model_construct(
            target_type="custom_type",
            spec_text="ユーザーがメールアドレスとパスワードを入力してログインする機能",
            supplemental_text="",
        )
        result = build_user_prompt(data)
        assert "custom_type" in result

    def test_output_contains_spec_text_section_header(self, valid_input_data):
        result = build_user_prompt(valid_input_data)
        assert "【仕様テキスト】" in result

    def test_output_contains_supplemental_section_header(self, valid_input_data):
        result = build_user_prompt(valid_input_data)
        assert "【補足情報】" in result
