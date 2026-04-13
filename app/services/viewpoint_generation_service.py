import logging
from typing import Optional
from app.domain.models import InputData, DisplayResult
from app.utils.input_validator import validate_input
from app.services.prompt_builder import build_system_prompt, build_user_prompt
from app.llm.openai_client import OpenAiClient
from app.llm.schemas import parse_llm_result
from app.services.result_formatter import to_display_result

logger = logging.getLogger(__name__)


class ViewpointGenerationService:
    def __init__(self, client: Optional[OpenAiClient] = None) -> None:
        self._client = client if client is not None else OpenAiClient()

    def generate(self, input_data: InputData) -> DisplayResult:
        validate_input(input_data)

        system_prompt = build_system_prompt()
        user_prompt = build_user_prompt(input_data)

        raw_text = self._client.generate_viewpoints(system_prompt, user_prompt)
        logger.debug("LLM raw response length: %d", len(raw_text))

        llm_result = parse_llm_result(raw_text)

        return to_display_result(llm_result)
