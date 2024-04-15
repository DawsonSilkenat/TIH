from enrich_places_api.cache_json import JsonFileCache
from enrich_places_api.places_lookup_google import GooglePlacesLookup
from llm_api.llm_queries_openai import OpenAILLMQueries
from llm_api.llm_models import LLMResponseType
from tih_api.tih_api import TIHAPI
from tih_api.format_api_response import format_api_response

from flask import Flask, render_template, request
import json
from datetime import datetime

# Creating the app and loading api keys 
app = Flask(__name__)
with open("api_keys.json", "r") as file:
    keys = json.load(file)
    tih_api_key = keys["TIH"]
    google_api_key = keys["GoogleAPI"]
    openai_api_key = keys["OpenAI"]
    model = keys["LLMModel"]
    max_tih_cache_age = keys["MaxCacheAgeTIHDataset"]

# For now I am just going to store the conversation. This should be replaced eventually, but good enough for poc
ai_conversation = []
view_conversation = []
cache = JsonFileCache('places_cache.json', 'places_cache_requests.json')
places_look_up = GooglePlacesLookup(google_api_key, cache)
tih_api = TIHAPI(tih_api_key, places_look_up, "tih_datasets_cache.json", max_tih_cache_age)
llm = OpenAILLMQueries(openai_api_key, model)

def append_to_conversation(data: dict):
    ai_conversation.append(data)
    #if data['role'] != 'tool' and 'content' in data:
    #    view_conversation.append(data)


def collect_data_and_respond():
    llm_answer = None
    api_response = llm.collect_user_data(ai_conversation)
    print(f"api_response: {api_response}")
    if api_response.response_type == LLMResponseType.TEXT:
        llm_answer = api_response.response_text.replace("**", "")
        append_to_conversation({"role": "assistant", "content": llm_answer})
    else:
        datasets = tih_api.get_datasets()
        datasets = llm.filter_datasets(ai_conversation, datasets)
        print(f"selected datasets: {datasets}")
        keywords = llm.get_query_keywords(ai_conversation)
        print(f"keywords: {keywords}")
        print(api_response.response_function_arguments)
        start_date = datetime.strptime(api_response.response_function_arguments["tripStartDate"], '%Y-%m-%d')
        end_date = datetime.strptime(api_response.response_function_arguments["tripEndDate"], '%Y-%m-%d')
        dk_api_responses = tih_api.multiple_datasets_by_keywords(datasets, keywords, 25, start_date, end_date)
        dk_api_responses = [format_api_response(response) for response in dk_api_responses]
        print(f"dk_api_responses: {dk_api_responses}")
        append_to_conversation({"role": "assistant", "tool_calls": api_response.response_tool_data})
        append_to_conversation({"role": "tool", "tool_call_id": api_response.response_tool_id, "content": "\n\n".join(dk_api_responses)})
        print(ai_conversation)
        collect_data_and_respond()

    return llm_answer


@app.route("/", methods=["GET", "POST"])
def handle_query():
    llm_answer = None
    user_query = None
    
    if request.method == "POST":
        user_query = request.form["user_input"]
        append_to_conversation({"role": "user", "content": user_query})
        collect_data_and_respond()

    return render_template("demo_page.html", conversations=ai_conversation)
    

if __name__ == "__main__":
    app.run()
