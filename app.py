from datasets import get_datasets
from keywords import get_query_keywords
from api_endpoint_functions.multiple_datasets import multiple_datasets_by_keywords
from generate_reply import process_api_responses
from flask import Flask, render_template, request
import json

# Creating the app and loading api keys 
app = Flask(__name__)
with open("api_keys.json", "r") as file:
    tih_api_key = json.load(file)["TIH"]


app.route("/", methods=["GET", "POST"])
def handle_query(user_query: str) -> str:
    """Entry point, taking a user's query as raw text, processing to find the correct api calls, and returning the result of those calls

    Args:
        user_query (str): The user's query
        tih_api_key (str): The user's TIH api key, under which the queries will be conducted
    """
    
    datasets = get_datasets(user_query, tih_api_key)
    keywords = get_query_keywords(user_query)
    
    
    # For now I am using just the Search Multiple Datasets By Keyword endpoint
    # This is the simplest, least work method. I would also like to look at doing each endpoint individually, but not MVP 
    # Concern: Even though this may pull from multiple datasets, I don't think there is any reason to expect it will
    api_responses = multiple_datasets_by_keywords(user_query, datasets, tih_api_key, keywords)
    
    # Here would be the place to look at deals, augment the information provided to the llm
    
    # Once we have the api responce we need the llm to process the response 
    llm_recommendations = process_api_responses(user_query, api_responses)
    
    return llm_recommendations
    
    

if __name__ == "__main__":
    app.run()
