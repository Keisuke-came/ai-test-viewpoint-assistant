import pytest
from unittest.mock import MagicMock, patch
from app.domain.models import LlmApiError


class TestOpenAiClient:
    def _make_mock_response(self, content: str) -> MagicMock:
        """OpenAI SDK のレスポンスオブジェクトを模倣するモックを作る。"""
        message = MagicMock()
        message.content = content
        choice = MagicMock()
        choice.message = message
        response = MagicMock()
        response.choices = [choice]
        return response

    @patch("app.llm.openai_client.OpenAI")
    def test_generate_viewpoints_returns_content_string(self, mock_openai_class, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        # settings モジュールのキャッシュを更新する
        import app.config.settings as settings
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")

        mock_instance = MagicMock()
        mock_openai_class.return_value = mock_instance
        mock_instance.chat.completions.create.return_value = self._make_mock_response(
            '{"summary": "s", "viewpoints": [], "ambiguities": [], "notes": []}'
        )

        from app.llm.openai_client import OpenAiClient
        client = OpenAiClient()
        result = client.generate_viewpoints("system", "user")
        assert isinstance(result, str)
        assert "summary" in result

    @patch("app.llm.openai_client.OpenAI")
    def test_generate_viewpoints_calls_with_correct_messages(self, mock_openai_class, monkeypatch):
        import app.config.settings as settings
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")

        mock_instance = MagicMock()
        mock_openai_class.return_value = mock_instance
        mock_instance.chat.completions.create.return_value = self._make_mock_response("response")

        from app.llm.openai_client import OpenAiClient
        client = OpenAiClient()
        client.generate_viewpoints("SYS", "USR")

        call_kwargs = mock_instance.chat.completions.create.call_args[1]
        messages = call_kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "SYS"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "USR"

    @patch("app.llm.openai_client.OpenAI")
    def test_generate_viewpoints_content_none_returns_empty_string(self, mock_openai_class, monkeypatch):
        import app.config.settings as settings
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")

        mock_instance = MagicMock()
        mock_openai_class.return_value = mock_instance
        mock_instance.chat.completions.create.return_value = self._make_mock_response(None)

        from app.llm.openai_client import OpenAiClient
        client = OpenAiClient()
        result = client.generate_viewpoints("s", "u")
        assert result == ""

    @patch("app.llm.openai_client.OpenAI")
    def test_openai_error_raises_llm_api_error(self, mock_openai_class, monkeypatch):
        from openai import OpenAIError
        import app.config.settings as settings
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")

        mock_instance = MagicMock()
        mock_openai_class.return_value = mock_instance
        mock_instance.chat.completions.create.side_effect = OpenAIError("API failure")

        from app.llm.openai_client import OpenAiClient
        client = OpenAiClient()
        with pytest.raises(LlmApiError) as exc_info:
            client.generate_viewpoints("s", "u")
        assert "AI呼び出しに失敗しました" in str(exc_info.value)

    def test_missing_api_key_raises_environment_error(self, monkeypatch):
        import app.config.settings as settings
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "")

        with pytest.raises(EnvironmentError):
            from app.llm.openai_client import OpenAiClient
            OpenAiClient()

    @patch("app.llm.openai_client.OpenAI")
    def test_response_format_json_object_used(self, mock_openai_class, monkeypatch):
        import app.config.settings as settings
        monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-key")

        mock_instance = MagicMock()
        mock_openai_class.return_value = mock_instance
        mock_instance.chat.completions.create.return_value = self._make_mock_response("{}")

        from app.llm.openai_client import OpenAiClient
        client = OpenAiClient()
        client.generate_viewpoints("s", "u")

        call_kwargs = mock_instance.chat.completions.create.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}
