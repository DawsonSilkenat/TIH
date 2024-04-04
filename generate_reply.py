import llm_functions
import re


def process_api_responses(user_query: str, api_responses: list[dict[str, any]]) -> str:
    # Initial processing to extract only the useful information from the api responses
    # What we consider useful may change over time, and this processing step might need to move to the api_endpoint_functions if it depends significantly on the api used
    
    api_responses = [_format_api_response(response) for response in api_responses]
    
    for response in api_responses:
        print(response)
        print()
    
    llm_api_processing_user_role = "\n".join(("Query:", 
                            user_query,
                            "",
                            "Context:",
                            "\n\n".join(api_responses),
                            "",
                            "The query relates to asking about things to do in Singapore.",
                            "The context is a list of relevant attractions in Singapore.",
                            "Provide a detailed response to the query using only the information from the provided context.",
                            "In addition to providing a list of options, you should try to provide some information about each option"))
    
    system_prompt = "\n".join((
        "Your task is to assist users with their visits to Singapore.",
        "At the very start of your message you will receive a query, which is exactly what the user asked.",
        "After the query, you will be provided with context. This context is a list of attractions in Singapore relevant to the user's query.",
        "The elements of the list are split by an empty line.",
        "Each element of the list starts with the name of the attractions, followed by a new line, followed by a description of the attraction",
        "You must provide a detailed response to the query using only the information from the provided context.",
        "In addition to providing a list of options, you should try to provide some information about each option in your answer."
    ))
    
    llm_api_processing_response = llm_functions.generate_llm_response(llm_api_processing_user_role, system_prompt=system_prompt)
    
    return llm_api_processing_response
    

def _format_api_response(api_response: dict[str, any]) -> str:
    """Transforms the dictionary returned by the api into a string which can be processed by the llm

    Args:
        api_response (dict[str, any]): The list of results from the API

    Returns:
        str: A string formatted to be interpretted by the llm
    """
    
    # For now we are only considering the name, description, and body for each response. 
    name = api_response["name"]
    description = api_response["description"]
    body = api_response["body"]
    
    # Some responses contain newlines to format more nicely for a human reader. Remove these as it may lead to confusion to a machine reader, especially since we are using newlines to distinguish between name, description and body.
    name = name.replace("\n", " ")
    description = description.replace("\n", " ")
    body = body.replace("\n", " ")
    
    # Some responses contain html, which doesn't add anything to the text and makes the result more difficult to read for debugging
    regex = r"<.*?>"
    
    name = re.sub(regex, "", name)
    description = re.sub(regex, "", description)
    body = re.sub(regex, "", body)
    
    
    # Regular expression to match any character outside the ASCII range
    # We remove such characters as they are unlikely to appear frequently, if at all, in llm training
    # TODO consider how I can exclude currency codes from this
    regex = r"[^\x00-\x7F]"
    
    name = re.sub(regex, "", name)
    description = re.sub(regex, "", description)
    body = re.sub(regex, "", body)
    
    return f"{name}\n{description}\n{body}"
    