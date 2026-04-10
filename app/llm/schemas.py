import json
from pydantic import ValidationError
from app.domain.models import LlmResult, ResponseFormatError


def parse_llm_result(raw_text: str) -> LlmResult:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ResponseFormatError(f"AI応答をJSONとして解釈できません: {e}") from e

    try:
        return LlmResult.model_validate(data)
    except ValidationError as e:
        raise ResponseFormatError(f"AI応答のスキーマが不正です: {e}") from e
