import json
import pytest
from unittest.mock import MagicMock
from app.domain.models import (
    DisplayResult,
    InputData,
    InputValidationError,
    LlmApiError,
    ResponseFormatError,
)
from app.services.viewpoint_generation_service import ViewpointGenerationService


def make_valid_raw_response() -> str:
    return json.dumps(
        {
            "summary": "テスト用サマリ",
            "viewpoints": [
                {
                    "category": "正常系",
                    "title": "正常ログイン",
                    "description": "正しい認証情報でログインできること",
                    "priority": "高",
                }
            ],
            "ambiguities": ["確認事項"],
            "notes": ["注意事項"],
        },
        ensure_ascii=False,
    )


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock()
    client.generate_viewpoints.return_value = make_valid_raw_response()
    return client


@pytest.fixture
def service(mock_client) -> ViewpointGenerationService:
    return ViewpointGenerationService(client=mock_client)


class TestViewpointGenerationServiceGenerate:
    def test_returns_display_result(self, service, valid_input_data):
        result = service.generate(valid_input_data)
        assert isinstance(result, DisplayResult)

    def test_summary_in_result(self, service, valid_input_data):
        result = service.generate(valid_input_data)
        assert result.summary == "テスト用サマリ"

    def test_grouped_viewpoints_in_result(self, service, valid_input_data):
        result = service.generate(valid_input_data)
        assert "正常系" in result.grouped_viewpoints

    def test_markdown_text_not_empty(self, service, valid_input_data):
        result = service.generate(valid_input_data)
        assert len(result.markdown_text) > 0

    def test_llm_client_called_once(self, service, mock_client, valid_input_data):
        service.generate(valid_input_data)
        mock_client.generate_viewpoints.assert_called_once()

    def test_system_and_user_prompts_passed_to_client(self, service, mock_client, valid_input_data):
        service.generate(valid_input_data)
        args = mock_client.generate_viewpoints.call_args[0]
        system_prompt, user_prompt = args[0], args[1]
        assert isinstance(system_prompt, str) and len(system_prompt) > 0
        assert isinstance(user_prompt, str) and len(user_prompt) > 0

    # --- 入力バリデーション異常系 ---

    def test_empty_spec_text_raises_input_validation_error(self, mock_client):
        data = InputData.model_construct(
            target_type="screen",
            spec_text="",
            supplemental_text="",
        )
        service = ViewpointGenerationService(client=mock_client)
        with pytest.raises(InputValidationError):
            service.generate(data)

    def test_short_spec_text_raises_input_validation_error(self, mock_client):
        # trim 後 19 文字（スペースパディングで Pydantic の min_length は回避）
        data = InputData.model_construct(
            target_type="screen",
            spec_text=" " + "あ" * 19,
            supplemental_text="",
        )
        service = ViewpointGenerationService(client=mock_client)
        with pytest.raises(InputValidationError):
            service.generate(data)

    # --- LLM API 異常系 ---

    def test_llm_api_error_propagates(self, mock_client, valid_input_data):
        mock_client.generate_viewpoints.side_effect = LlmApiError("API失敗")
        service = ViewpointGenerationService(client=mock_client)
        with pytest.raises(LlmApiError):
            service.generate(valid_input_data)

    # --- 応答フォーマット異常系 ---

    def test_invalid_json_response_raises_response_format_error(self, mock_client, valid_input_data):
        mock_client.generate_viewpoints.return_value = "これはJSONではありません"
        service = ViewpointGenerationService(client=mock_client)
        with pytest.raises(ResponseFormatError):
            service.generate(valid_input_data)

    def test_invalid_schema_response_raises_response_format_error(self, mock_client, valid_input_data):
        mock_client.generate_viewpoints.return_value = json.dumps({"invalid_key": "no_summary"})
        service = ViewpointGenerationService(client=mock_client)
        with pytest.raises(ResponseFormatError):
            service.generate(valid_input_data)

    def test_empty_viewpoints_in_response_returns_display_result(self, mock_client, valid_input_data):
        mock_client.generate_viewpoints.return_value = json.dumps(
            {"summary": "s", "viewpoints": [], "ambiguities": [], "notes": []}
        )
        service = ViewpointGenerationService(client=mock_client)
        result = service.generate(valid_input_data)
        assert isinstance(result, DisplayResult)
        assert result.grouped_viewpoints == {}
