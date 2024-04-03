import requests
import llm_functions

def get_datasets(user_query: str, tih_api_key: str) -> list[str]:
    possible_datasets = _request_dataset_list(tih_api_key)
    return _filter_datasets(possible_datasets, user_query)


def _request_dataset_list(tih_api_key: str) -> list[str]:
    """Use the TIH api to fetch the list of possible datasets
    
    Args:
        tih_api_key (str): The user's TIH api key, under which the queries will be conducted
        
    Returns:
        list[str]: the list of available datasets
    """
    
    url = "https://api.stb.gov.sg/content/common/v2/datasets"
    headers = {
        "X-API-Key" : tih_api_key, 
        "Content-Type" : "application/json"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("data")
    response.raise_for_status()
    

def _filter_datasets(possible_datasets: list[str], user_query: str) -> list[str]:
    """We would like to reduce possible_datasets to only those related to the user's query. We do this using a large language model

    Args:
        possible_datasets (list[str]): The list of all possible datasets
        user_query (str): What the user has asked

    Returns:
        list[str]: The elements of possible_datasets which are relevant to the user's query
    """
    
    str_possible_datasets = ", ".join(possible_datasets)
    llm_filtering_request = "\n".join(("Query:", 
                            user_query,
                            "",
                            "I would like to know which of the following categories most likely contains the answer to the user's query:",str_possible_datasets,
                            "",
                            "Your response should be a comma seperated list of categories and nothing else"))
    
    print(llm_filtering_request)
    filtering_response = llm_functions.generate_llm_response(llm_filtering_request)
    
    # TODO there will likely need to be some processing here which converts back to a list of strings.
    # I have added a placeholder, but it may require adjustments depending on llm selected
    filtering_response = filtering_response.split(",")
    
    return filtering_response
