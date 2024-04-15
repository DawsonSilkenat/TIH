from typing import Iterable
from openai import OpenAI, NotGiven, NOT_GIVEN
from openai.types.chat import ChatCompletionMessageParam
import json
import time

from llm_api.llm_queries_interface import ILLMQueries
from llm_api.llm_models import LLMResponse, LLMResponseType


class OpenAILLMQueries(ILLMQueries):
    def __init__(self, api_key, model):
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def _generate_llm_response(self, conversation: list[dict[str, str]], response_start: str = None, system_prompt: str = None,
                              tools: Iterable[ChatCompletionMessageParam] | NotGiven = NOT_GIVEN) -> LLMResponse:
        messages = []

        if system_prompt is not None:
            messages.append({"role": "system", "content": system_prompt})

        messages = messages + conversation

        if response_start is not None:
            messages.append({"role": "assistant", "content": response_start})

        start = time.time()
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            tools=tools)
        end = time.time()
        print(f"LLM request took {end - start} seconds")

        #print(response)
        if response.choices[0].finish_reason == 'tool_calls':
            tool_call = response.choices[0].message.tool_calls[0]
            return LLMResponse(LLMResponseType.FUNCTION, "", tool_call.id, tool_call.function.name,
                               json.loads(tool_call.function.model_dump()['arguments']),
                               response.choices[0].message.tool_calls)
        else:
            return LLMResponse(LLMResponseType.TEXT, response.choices[0].message.content, "", "", dict(), list())

    def collect_user_data(self, conversation: list[dict[str, str]]) -> LLMResponse:
        system_prompt = """
        You are a helpful tourist assistant for Singapore. Every question the user makes relates to visiting singapore. 
        In order to help someone to find the right spot to visit for a 
        given topic you need the start and end date when they visiting Singapore
        and weather the person visiting as individual or group. 
        For an individual- just ask the age of the person. 
        If It is for a group - we need to know how many people are on it and what there ages are for each person. 
        If the group contains people below 16 year old the recommendation must be children friendly.
        Only ask one question at the time.
    
        Only when you have collect the following information Topic, Individual or group, children friendly or not, 
        trip start and end date, topic preferences, within the topic you can call the function getRecommendations.
    
        If you retrieved the list of recommendations from the function 
        select up to 5 recommendations that best matches the provided user information.
        Between each recommendation item a line break needs to be inserted.
        Format the recommendations as plain text. 
        Remove any markdown formatting
        Include the Restaurant name, Description, Website, Address and rating information for each recommendations if available.
        """

        return self._generate_llm_response(conversation, system_prompt=system_prompt, tools=[{
            "type": "function",
            "function": {
                "name": "getRecommendations",
                "description": "Get recommendations for the users request",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recommendationTopic": {
                            "type": "string",
                            "description": "topic for which the user requests a recommendation"
                        },
                        "tripStartDate": {
                            "type": "string",
                            "description": "date when the trip starts. Format=YYYY-MM-DD",
                        },
                        "tripEndDate": {
                            "type": "string",
                            "description": "date when the trip ends. Format=YYYY-MM-DD",
                        },
                        "groupSize": {
                            "type": "integer",
                            "description": "number of people"
                        },
                        "familyFriendly": {
                            "type": "boolean",
                            "description": "Indicates whether the recommendation needs to be family friendly"
                        },
                        "topicPreferences": {
                            "type": "string",
                            "description": "preferences that relates to the given user topic."
                        },
                        "priceLevel": {
                            "type": "integer",
                            "description": ""
                        }
                    }
                }
            }
        }])

    def get_query_keywords(self, conversation: list[dict[str, str]]) -> list[str]:
        system_prompt = """ Your are supporting with breaking down a conversation that want to get activity recommendations 
        during there vacation. The conversation should be broken down into a few important keywords provided by the user.
        The result should contain a maximum of 10 keywords.
        The keywords must be valid url arguments therefore characters such as / or . are not allowed.
        Your response should be only keywords comma separated and nothing else
        
        Conversation:
        user: I want to visit some music event.
        assistant: What are your music preferences?
        user: I like techno and rock.
        assistant: How long do you stay in singapore?
        user: from 01/03/23 to 20/03/23.
        assistant: Are you visiting singapore alone or in a group?
        user: with my family.
        assistant: how many people and how old are they?
        user: 4 people: 35, 36, 7, 8
        assistant: Therefore it needs to be family friendly?
        user: yes
    
        Result: family-friendly, children, music, techno, rock
    
        Conversation: <conversation>.
        Results: 
        """
        start = time.time()
        simplified_conversation = list()
        for data in conversation:
            if 'content' in data:
                simplified_conversation.append(f"{data['role']}: {data['content']}")

        system_prompt = system_prompt.replace("<conversation>", "\n".join(simplified_conversation))

        keywords_response = self._generate_llm_response(list(), system_prompt=system_prompt).response_text
        end = time.time()
        print(f"Keywords LLM request took {end - start} seconds")
        return keywords_response.split(", ")

    def filter_datasets(self, conversation: list[dict[str, str]], possible_datasets: list[str]) -> list[str]:
        """We would like to reduce possible_datasets to only those related to the user's query.
        We do this using a large language model

        Args:
            conversation (list[dict[str, str]]): Conversation between the user and llm

        Returns:
            list[str]: The elements of possible_datasets which are relevant to the user's query
        """
        start = time.time()
        str_possible_datasets = ", ".join(possible_datasets)
        str_conversation = ""
        for message in conversation:
            if 'tool' != message['role'] and 'content' in message:
                str_conversation = f"{str_conversation}\n{message['role']}:{message['content']}"

        system_prompt = "\n".join((
            "Your task is to choose which of the following categories fits best for the given conversation.",
            "If multiple categories fit choose the category that fits best with the latest part of the conversation",
            "categories:",
            str_possible_datasets,
            "",
            "conversation:",
            str_conversation,
            "",
            "Your response should be one category if possible otherwise a comma separated list of categories and nothing else"
        ))

        filtered_datasets = self._generate_llm_response(list(), system_prompt=system_prompt).response_text
        filtered_datasets = filtered_datasets.split(",")
        filtered_datasets = [item.strip() for item in filtered_datasets]
        end = time.time()
        print(f"Dataset filter LLM request took {end - start} seconds")
        return filtered_datasets
