import requests

def multiple_datasets_by_keywords(datasets: list[str], tih_api_key: str) -> str:
    pass
  

def _request_from_api(datasets: list[str], tih_api_key: str, keywords: list[str]=None) -> dict[str, any]:
    url = "https://api.stb.gov.sg/content/common/v2/search"
    headers = {
        "X-API-Key" : tih_api_key, 
        "Content-Type" : "application/json",
        "X-Content-Language" : "en"
    }
    
    query = {
        "dataset" : ", ".join(datasets),
        "distinct" : "Yes",
        "limit" : 50
    }
    
    if keywords is not None:
        query["keyword"] = ", ".join(keywords)
        
    
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    response.raise_for_status()