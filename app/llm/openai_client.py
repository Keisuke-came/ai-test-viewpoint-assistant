import logging
from openai import OpenAI, OpenAIError
from app.config import settings
from app.domain.models import LlmApiError

logger = logging.getLogger(__name__)


class OpenAiClient:
    def __init__(self) -> None:
        settings.validate_settings()
        self._client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.OPENAI_TIMEOUT_SECONDS,
        )
        self._model = settings.OPENAI_MODEL

    def generate_viewpoints(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content or ""
        except OpenAIError as e:
            logger.error("OpenAI API error: %s", e)
            raise LlmApiError(f"AI呼び出しに失敗しました: {e}") from e
