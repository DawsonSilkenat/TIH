import requests

def multiple_datasets_by_keywords(conversation: list[dict[str, str]], datasets: list[str], tih_api_key: str, keywords: list[str], limit: int) -> list[dict[str, any]]:
    # Placeholder for getting additional parameters from the user's query
    
    api_response = _request_from_api(datasets, tih_api_key, keywords, limit)
    
    # Any processing would go here, but probably best to just return the full response
    
    return api_response
  

def _request_from_api(datasets: list[str], tih_api_key: str, keywords: list[str], limit: int) -> list[dict[str, any]]:
    url = "https://api.stb.gov.sg/content/common/v2/search"
    headers = {
        "X-API-Key" : tih_api_key, 
        "Content-Type" : "application/json",
        "X-Content-Language" : "en"
    }
    
    query = {
        "dataset" : ", ".join(datasets),
        "distinct" : "Yes",
        "limit" : limit, 
        "keyword" : ", ".join(keywords)
    }
    
    
    response = requests.get(url, headers=headers, params=query)
    
    if response.status_code == 200:
        return response.json()["data"]
    response.raise_for_status()