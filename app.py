from datasets import get_datasets
from keywords import get_query_keywords
from api_endpoint_functions.multiple_datasets import multiple_datasets_by_keywords

def handle_query(user_query: str, tih_api_key: str) -> str:
    """Entry point, taking a user's query as raw text, processing to find the correct api calls, and returning the result of those calls

    Args:
        user_query (str): The user's query
        tih_api_key (str): The user's TIH api key, under which the queries will be conducted
    """
    
    datasets = get_datasets(user_query, tih_api_key)
    keywords = get_query_keywords(user_query)
    
    
    # For now I am using just the Search Multiple Datasets By Keyword endpoint
    # This is the simplest, least work method. I would also like to look at doing each endpoint individually 
    multiple_datasets_by_keywords(user_query, datasets, keywords, tih_api_key)
    
    
    



if __name__ == "__main__":
    import json

    with open("api_keys.json", "r") as file:
        tih_api_key = json.load(file)["TIH"]
        
    handle_query(None, tih_api_key)
