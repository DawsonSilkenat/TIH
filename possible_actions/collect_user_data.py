import llm_functions
from llm_functions import LLMResponse


def collect_user_data(conversation: list[dict[str, str]]) -> LLMResponse:

    system_prompt = """
    You are a helpful tourist assistant for Singapore. Every question the user makes relates to visiting singapore. 
    In order to help someone to find the right spot to visit for a 
    given topic you need the start and end date when they visiting Singapore
    and weather the person visiting as individual or group. 
    For an individual- just ask the age of the person. 
    If It is for a group - we need to know how many people are on it and what there ages are for each person. 
    If the group contains people below 16 year old the recommendation must be children friendly.
    Only ask one question at the time.
    Only when you have collect all required information Topic, Individual or group, recommendation must the children friendly, 
    trip start and end date, preferences within the topic you can call the function getRecommendations.
    
    If you retrieved the list of recommendations from the function 
    select up to 5 recommendations that best matches the provided user information.
    Between each recommendation item a line break needs to be inserted.
    """
    
    return llm_functions.generate_llm_response(conversation, system_prompt=system_prompt, tools=[{
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
                                "tripStartDate":{
                                    "type": "string",
                                    "description": "date when the trip starts",
                                },
                                "tripEndDate": {
                                    "type": "string",
                                    "description": "date when the trip ends",
                                },
                                "groupSize": {
                                    "type": "integer",
                                    "description": "number of people"
                                },
                                "familyFriendly": {
                                    "type": "boolean",
                                    "description": "Indicates whether the recommendation needs to be family friendly"
                                },
                                "preferences": {
                                    "type": "string",
                                    "description": "preferences that relates to the given user topic."
                                }
                            }
                    },
                    "required": ["recommendationTopic", "tripStartDate", "tripEndDate", "groupSize", "familyFriendly", "preferences"]
                }
        }])