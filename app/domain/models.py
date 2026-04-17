from typing import Any, List, Literal
from pydantic import BaseModel, Field, field_validator


class InputData(BaseModel):
    target_type: Literal["screen", "api", "batch", "ticket", "other"]
    spec_text: str = Field(min_length=20)
    supplemental_text: str = ""


class Viewpoint(BaseModel):
    category: str
    title: str
    description: str
    priority: Literal["高", "中", "低"]


class LlmResult(BaseModel):
    summary: str
    viewpoints: List[Viewpoint]
    ambiguities: List[str]
    notes: List[str]

    @field_validator("ambiguities", "notes", mode="before")
    @classmethod
    def coerce_str_to_list(cls, v: Any) -> Any:
        """LLM が文字列を返した場合にリストへ変換する。

        LLM が ambiguities / notes を単一の文字列として返すことがある。
        その場合は 1 要素のリストに変換して ValidationError を防ぐ。
        """
        if isinstance(v, str):
            return [v] if v.strip() else []
        return v


class DisplayResult(BaseModel):
    summary: str
    grouped_viewpoints: dict[str, list[Viewpoint]]
    ambiguities: list[str]
    notes: list[str]
    markdown_text: str


class InputValidationError(Exception):
    pass


class LlmApiError(Exception):
    pass


class ResponseFormatError(Exception):
    pass


class ApplicationError(Exception):
    pass
