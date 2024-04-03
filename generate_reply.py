import llm_functions
import re


def process_api_responses(user_query: str, api_responses: list[dict[str, any]]) -> str:
    # Initial processing to extract only the useful information from the api responses
    # What we consider useful may change over time, and this processing step might need to move to the api_endpoint_functions if it depends significantly on the api used
    
    api_responses = [_format_api_response(response) for response in api_responses]
    print(api_responses)
    
    llm_api_processing_request = "\n".join(("Query:", 
                            user_query,
                            "",
                            "Context:",
                            "\n\n".join(api_responses),
                            "",
                            "The query relates to asking about things to do in Singapore.",
                            "The context is a list of relevant attractions in Singapore.",
                            "Provide a detailed response to the query using only the information from the provided context."))
    llm_api_processing_response = llm_functions.generate_llm_response(llm_api_processing_request)
    
    return llm_api_processing_response
    

def _format_api_response(api_response: dict[str, any]) -> str:
    
    # For now we are only considering the name, description, and body for each response. 
    name = api_response["name"]
    description = api_response["description"]
    body = api_response["body"]
    
    # Some responses contain newlines to format more nicely for a human reader. Remove these as it may lead to confusion to a machine reader, especially since we are using newlines to distinguish between name, description and body.
    name = name.replace("\n", " ")
    description = description.replace("\n", " ")
    body = body.replace("\n", " ")
    
    # Regular expression to match any character outside the ASCII range
    # We remove such characters as they are unlikely to appear frequently, if at all, in llm training
    # TODO consider how I can exclude currency codes from this
    regex = r"[^\x00-\x7F]"
    
    name = re.sub(regex, "", name)
    description = re.sub(regex, "", description)
    body = re.sub(regex, "", body)
    
    return f"{name}\n{description}\n{body}"
    