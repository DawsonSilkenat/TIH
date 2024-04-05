import llm_functions


def answer_user_query(conversation: list[dict[str, str]], api_responses: list[str]) -> str:

    
    system_prompt = "\n".join((
        "Your task is to assist users with their visits to Singapore.",
        "To help you with this task, here is a list of relevant attractions in Singapore",
        "The elements of the list are split by an empty line.",
        "Each element of the list starts with the name of the attractions, followed by a new line, followed by a description of the attraction",
        "",
        "attractions:",
        "\n\n".join(api_responses),
        "",
        "You must provide a detailed answer to the user's query using only the information from the provided list of attractions.",
        "In addition to providing a list of attractions, you should try to provide some information about each attraction in your answer.",
        "Alternatively, you may ask the user questions to help provide a more personalised suggestion."
    ))
    
    llm_answer = llm_functions.generate_llm_response(conversation, system_prompt=system_prompt)
    
    # chatgpt sometimes thinks it is writing markdown, so sometimes uses ** to make words bold. This doesn't work, either because it isn't valid html or because flask escapes it
    llm_answer = llm_answer.replace("**", "") 
    
    return llm_answer
    


    