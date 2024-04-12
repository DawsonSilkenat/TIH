from dataclasses import dataclass
from enum import Enum


class LLMResponseType(Enum):
    UNKNOWN = 0
    TEXT = 1
    FUNCTION = 2


@dataclass(frozen=True)
class LLMResponse:
    response_type: LLMResponseType
    response_text: str
    response_tool_id: str
    response_function_name: str
    response_function_arguments: dict
    response_tool_data: list

