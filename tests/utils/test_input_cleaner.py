import pytest
from app.domain.models import InputValidationError
from app.utils.input_cleaner import clean, validate_length, truncate


class TestClean:
    def test_strips_leading_and_trailing_whitespace(self):
        assert clean("  hello  ") == "hello"

    def test_strips_leading_and_trailing_newlines(self):
        assert clean("\nhello\n") == "hello"

    def test_replaces_tab_with_single_space(self):
        assert clean("foo\tbar") == "foo bar"

    def test_replaces_multiple_tabs(self):
        assert clean("a\t\tb") == "a  b"

    def test_compresses_3_consecutive_blank_lines_to_2(self):
        text = "a\n\n\nb"
        result = clean(text)
        assert result == "a\n\nb"

    def test_compresses_4_consecutive_blank_lines_to_2(self):
        text = "a\n\n\n\nb"
        result = clean(text)
        assert result == "a\n\nb"

    def test_2_consecutive_blank_lines_unchanged(self):
        text = "a\n\nb"
        result = clean(text)
        assert result == "a\n\nb"

    def test_strips_trailing_spaces_per_line(self):
        text = "hello   \nworld   "
        result = clean(text)
        assert result == "hello\nworld"

    def test_empty_string_returns_empty(self):
        assert clean("") == ""

    def test_whitespace_only_returns_empty(self):
        assert clean("   \t\n  ") == ""

    def test_processing_order_tab_then_blank_compression(self):
        # タブ置換→空行圧縮→行末空白除去 の順が正しく適用される
        # "a\t\n\n\nb" → タブをスペースに → "a \n\n\nb"
        # → 3連続空行圧縮 → "a \n\nb"
        # → 行末空白除去 → "a\n\nb"
        text = "a\t\n\n\nb"
        result = clean(text)
        assert "\t" not in result
        assert result == "a\n\nb"

    def test_normal_text_unchanged(self):
        text = "hello\nworld"
        assert clean(text) == "hello\nworld"


class TestValidateLength:
    def test_within_limit_no_exception(self):
        validate_length("abc", 3)  # 例外なし

    def test_exactly_at_limit_no_exception(self):
        validate_length("abc", 3)

    def test_one_under_limit_no_exception(self):
        validate_length("ab", 3)

    def test_exceeds_limit_raises(self):
        with pytest.raises(InputValidationError) as exc_info:
            validate_length("abcd", 3)
        assert "上限（3文字）" in str(exc_info.value)
        assert "現在: 4文字" in str(exc_info.value)

    def test_error_message_contains_max_chars(self):
        with pytest.raises(InputValidationError) as exc_info:
            validate_length("a" * 101, 100)
        assert "100" in str(exc_info.value)
        assert "101" in str(exc_info.value)

    def test_max_chars_zero_raises(self):
        with pytest.raises(InputValidationError) as exc_info:
            validate_length("a", 0)
        assert "1以上を指定してください" in str(exc_info.value)

    def test_max_chars_negative_raises(self):
        with pytest.raises(InputValidationError) as exc_info:
            validate_length("a", -1)
        assert "1以上を指定してください" in str(exc_info.value)

    def test_max_chars_one_with_empty_text_no_exception(self):
        validate_length("", 1)  # 0 <= 1 → 例外なし

    def test_returns_none_on_success(self):
        result = validate_length("hello", 10)
        assert result is None


class TestTruncate:
    def test_text_shorter_than_max_returned_as_is(self):
        assert truncate("abc", 5) == "abc"

    def test_text_equal_to_max_returned_as_is(self):
        assert truncate("abc", 3) == "abc"

    def test_text_longer_than_max_truncated(self):
        assert truncate("abcde", 3) == "abc"

    def test_truncate_to_1_char(self):
        assert truncate("hello", 1) == "h"

    def test_max_chars_zero_raises(self):
        with pytest.raises(InputValidationError) as exc_info:
            truncate("abc", 0)
        assert "1以上を指定してください" in str(exc_info.value)

    def test_max_chars_negative_raises(self):
        with pytest.raises(InputValidationError) as exc_info:
            truncate("abc", -5)
        assert "1以上を指定してください" in str(exc_info.value)

    def test_empty_string_with_valid_max_returned_as_is(self):
        assert truncate("", 10) == ""

    def test_multibyte_chars_counted_by_len(self):
        # 日本語文字は len() で1文字としてカウント
        assert truncate("あいうえお", 3) == "あいう"

    def test_truncate_does_not_raise_on_boundary(self):
        result = truncate("ab", 2)
        assert result == "ab"
