import pytest
from pydantic import ValidationError
from app.domain.models import InputData, InputValidationError
from app.utils.input_validator import validate_input


def make_input(spec_text: str, supplemental_text: str = "") -> InputData:
    """InputData を直接構築してバリデーションをバイパスするヘルパー。
    Pydantic の min_length=20 を回避して validate_input 単体をテストしたい場合に使う。
    """
    return InputData.model_construct(
        target_type="screen",
        spec_text=spec_text,
        supplemental_text=supplemental_text,
    )


class TestValidateInput:
    def test_valid_input_no_exception(self, valid_input_data):
        # 正常な入力では例外なし
        validate_input(valid_input_data)

    def test_spec_text_empty_raises(self):
        data = make_input("")
        with pytest.raises(InputValidationError) as exc_info:
            validate_input(data)
        assert "仕様テキストを入力してください" in str(exc_info.value)

    def test_spec_text_whitespace_only_raises(self):
        # スペースのみは空文字扱い
        data = make_input("   ")
        with pytest.raises(InputValidationError) as exc_info:
            validate_input(data)
        assert "仕様テキストを入力してください" in str(exc_info.value)

    def test_spec_text_newlines_only_raises(self):
        data = make_input("\n\n\n")
        with pytest.raises(InputValidationError) as exc_info:
            validate_input(data)
        assert "仕様テキストを入力してください" in str(exc_info.value)

    def test_spec_text_trim_result_19_chars_raises(self):
        # trim 後 19 文字 → 短すぎるエラー
        # (先頭スペースを足して Pydantic の min_length=20 は通過させる)
        spec = " " + "あ" * 19  # 合計20文字だが trim 後 19 文字
        data = make_input(spec)
        with pytest.raises(InputValidationError) as exc_info:
            validate_input(data)
        assert "短すぎます" in str(exc_info.value)

    def test_spec_text_trim_result_20_chars_ok(self):
        # trim 後ちょうど 20 文字 → 例外なし
        spec = "  " + "あ" * 20  # trim 後 20 文字
        data = make_input(spec)
        validate_input(data)  # 例外が起きなければ OK

    def test_spec_text_trim_result_21_chars_ok(self):
        spec = "あ" * 21
        data = make_input(spec)
        validate_input(data)

    def test_supplemental_text_not_checked(self):
        # supplemental_text は validate_input では検証しない
        data = make_input("あ" * 20, supplemental_text="")
        validate_input(data)  # 例外なし
