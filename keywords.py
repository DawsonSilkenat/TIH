import llm_functions


def get_query_keywords(user_query: str) -> list[str]:
    llm_keywords_request = "\n".join(("Query:", 
                             user_query,
                             "",
                            "I need to know very precisely what the user is searching for, in the form of keywords",
                            "Your response should be a comma seperated list of keywords and nothing else"))
    keywords_response = llm_functions.generate_llm_response(llm_keywords_request)
    
    # TODO there will likely need to be some processing here which converts back to a list of strings.
    # I have added a placeholder, but it may require adjustments depending on llm selected
    keywords_response = keywords_response.split(", ")
    
    return keywords_response