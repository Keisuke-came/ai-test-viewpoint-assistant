from pydantic import BaseModel, Field
from typing import Literal


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
    viewpoints: list[Viewpoint]
    ambiguities: list[str]
    notes: list[str]


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
