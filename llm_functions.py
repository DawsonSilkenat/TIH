from typing import Iterable

from openai import OpenAI, NotGiven, NOT_GIVEN
import json
from enum import Enum
from dataclasses import dataclass

from openai.types.chat import ChatCompletionMessageParam

with open("api_keys.json", "r") as file:
    keys = json.load(file)
    openAI_api_key = keys["OpenAI"]
client = OpenAI(api_key=openAI_api_key)


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


def generate_llm_response(conversation: list[dict[str, str]], response_start: str = None, system_prompt: str = None,
                          tools: Iterable[ChatCompletionMessageParam] | NotGiven = NOT_GIVEN) \
        -> LLMResponse:
    messages = []
    
    if system_prompt is not None:
        messages.append({"role": "system", "content": system_prompt})
        
    messages = messages + conversation
    
    if response_start is not None:
        messages.append({"role": "assistant", "content": response_start})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages=messages,
        tools=tools)

    print(response)
    if response.choices[0].finish_reason == 'tool_calls':
        tool_call = response.choices[0].message.tool_calls[0]
        return LLMResponse(LLMResponseType.FUNCTION, "", tool_call.id, tool_call.function.name,
                           tool_call.function.model_dump(), response.choices[0].message.tool_calls)
    else:
        return LLMResponse(LLMResponseType.TEXT, response.choices[0].message.content, "", "", dict(), list())
