import json
import pytest
from app.domain.models import LlmResult, ResponseFormatError
from app.llm.schemas import parse_llm_result


def make_valid_json(**overrides) -> str:
    base = {
        "summary": "テスト用サマリ",
        "viewpoints": [
            {
                "category": "正常系",
                "title": "正常ログイン",
                "description": "正しい認証情報でログインできること",
                "priority": "高",
            }
        ],
        "ambiguities": ["確認事項A"],
        "notes": ["注意事項B"],
    }
    base.update(overrides)
    return json.dumps(base, ensure_ascii=False)


class TestParseLlmResult:
    def test_valid_json_returns_llm_result(self):
        raw = make_valid_json()
        result = parse_llm_result(raw)
        assert isinstance(result, LlmResult)
        assert result.summary == "テスト用サマリ"

    def test_viewpoints_parsed_correctly(self):
        raw = make_valid_json()
        result = parse_llm_result(raw)
        assert len(result.viewpoints) == 1
        assert result.viewpoints[0].category == "正常系"
        assert result.viewpoints[0].priority == "高"

    def test_empty_viewpoints_allowed(self):
        raw = make_valid_json(viewpoints=[])
        result = parse_llm_result(raw)
        assert result.viewpoints == []

    def test_empty_ambiguities_allowed(self):
        raw = make_valid_json(ambiguities=[])
        result = parse_llm_result(raw)
        assert result.ambiguities == []

    def test_empty_notes_allowed(self):
        raw = make_valid_json(notes=[])
        result = parse_llm_result(raw)
        assert result.notes == []

    def test_multiple_viewpoints(self):
        viewpoints = [
            {"category": "正常系", "title": "A", "description": "d", "priority": "高"},
            {"category": "異常系", "title": "B", "description": "d", "priority": "中"},
        ]
        raw = make_valid_json(viewpoints=viewpoints)
        result = parse_llm_result(raw)
        assert len(result.viewpoints) == 2

    # --- 異常系 ---

    def test_invalid_json_raises_response_format_error(self):
        with pytest.raises(ResponseFormatError) as exc_info:
            parse_llm_result("これはJSONではありません")
        assert "JSON" in str(exc_info.value)

    def test_empty_string_raises_response_format_error(self):
        with pytest.raises(ResponseFormatError):
            parse_llm_result("")

    def test_missing_summary_raises_response_format_error(self):
        data = {
            "viewpoints": [],
            "ambiguities": [],
            "notes": [],
        }
        with pytest.raises(ResponseFormatError):
            parse_llm_result(json.dumps(data))

    def test_missing_viewpoints_raises_response_format_error(self):
        data = {
            "summary": "s",
            "ambiguities": [],
            "notes": [],
        }
        with pytest.raises(ResponseFormatError):
            parse_llm_result(json.dumps(data))

    def test_invalid_priority_raises_response_format_error(self):
        viewpoints = [
            {"category": "正常系", "title": "A", "description": "d", "priority": "最高"},
        ]
        raw = make_valid_json(viewpoints=viewpoints)
        with pytest.raises(ResponseFormatError):
            parse_llm_result(raw)

    def test_viewpoints_not_list_raises_response_format_error(self):
        data = {
            "summary": "s",
            "viewpoints": "not a list",
            "ambiguities": [],
            "notes": [],
        }
        with pytest.raises(ResponseFormatError):
            parse_llm_result(json.dumps(data))

    def test_ambiguities_string_is_coerced_to_list(self):
        # LLM が文字列を返した場合は 1 要素のリストに変換する
        data = {
            "summary": "s",
            "viewpoints": [],
            "ambiguities": "要確認事項あり",
            "notes": [],
        }
        result = parse_llm_result(json.dumps(data))
        assert result.ambiguities == ["要確認事項あり"]

    def test_notes_string_is_coerced_to_list(self):
        # LLM が文字列を返した場合は 1 要素のリストに変換する
        data = {
            "summary": "s",
            "viewpoints": [],
            "ambiguities": [],
            "notes": "注意事項あり",
        }
        result = parse_llm_result(json.dumps(data))
        assert result.notes == ["注意事項あり"]

    def test_json_array_instead_of_object_raises(self):
        with pytest.raises(ResponseFormatError):
            parse_llm_result("[]")
