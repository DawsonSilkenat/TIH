import llm_functions


def get_query_keywords(conversation: list[dict[str, str]]) -> list[str]:
    system_prompt = "\n".join((
        "Your task is to provide a list of keywords which indecate what content the user is searching for.",
        "Your response should be a comma seperated list of keywords and nothing else."
    ))
    
    keywords_response = llm_functions.generate_llm_response(conversation, system_prompt=system_prompt)
    
    keywords_response = keywords_response.split(", ")
    
    return keywords_response