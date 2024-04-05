import llm_functions

def get_more_information(conversation: list[dict[str, str]], api_responses: list[str]) -> str:
    
    system_prompt = "\n".join((
        "Your task is to assist users with their visits to Singapore.",
        "You are currently asking the user questions so that you can better answer their query.",
        "Here is a list of attractions in Singapore believed to possibly be related to the user's query",
        "The elements of the list are split by an empty line.",
        "Each element of the list starts with the name of the attractions, followed by a new line, followed by a description of the attraction",
        "",
        "attractions:",
        "\n\n".join(api_responses),
        "",
        "Your questions should relate to characteristics present in the list of attractions"
    ))
    
    followup_question = llm_functions.generate_llm_response(conversation, system_prompt=system_prompt)
    
    print(followup_question)
    
    return followup_question