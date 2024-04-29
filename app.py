from flask import Flask, render_template, request
import json
import os

# Creating the app and loading api keys 
app = Flask(__name__)
with open("api_keys.json", "r") as file:
    keys = json.load(file)
    tih_api_key = keys["TIH"]
    if 'GoogleAPI' in keys:
        google_api_key = keys["GoogleAPI"]
    else:
        google_api_key = None
    openai_api_key = keys["OpenAI"]
    os.environ["OPENAI_API_KEY"] = openai_api_key
    model = keys["LLMModel"]
    download_images = keys['download_places_image']
    max_tih_cache_age = keys["MaxCacheAgeTIHDataset"]


from enrich_places_api.cache_json import JsonFileCache
from enrich_places_api.places_lookup_google import GooglePlacesLookup
from llm_api.llm_queries_openai import OpenAILLMQueries
from llm_api.llm_models import LLMResponseType
from tih_api.tih_api import TIHAPI
from tih_api.format_api_response import format_api_response
import re
from datetime import datetime


# For now I am just going to store the conversation. This should be replaced eventually, but good enough for poc
ai_conversation = []
view_conversation = []
cache = JsonFileCache('places_cache.json', 'places_cache_requests.json')
places_look_up = GooglePlacesLookup(google_api_key, cache, download_images)
tih_api = TIHAPI(tih_api_key, places_look_up, "tih_datasets_cache.json", max_tih_cache_age)
llm = OpenAILLMQueries(openai_api_key, model)


def append_to_conversation(data: dict):
    ai_conversation.append(data)
    view_conversation.append(data)


def collect_data_and_respond():
    api_response = llm.collect_user_data(ai_conversation)
    print(f"api_response: {api_response}")
    if api_response.response_type == LLMResponseType.TEXT:
        llm_answer = api_response.response_text.replace("**", "")
        append_to_conversation({"role": "assistant", "content": llm_answer})
    else:
        create_recommendation_response(api_response)


def create_recommendation_response(api_response):
    datasets = tih_api.get_datasets()
    datasets = llm.filter_datasets(ai_conversation, datasets)
    print(f"selected datasets: {datasets}")
    keywords = llm.get_query_keywords(ai_conversation)
    print(f"keywords: {keywords}")
    print(api_response.response_function_arguments)
    start_date = datetime.strptime(api_response.response_function_arguments["tripStartDate"], '%Y-%m-%d')
    end_date = datetime.strptime(api_response.response_function_arguments["tripEndDate"], '%Y-%m-%d')
    dk_api_responses_raw = tih_api.multiple_datasets_by_keywords(datasets, keywords, 25, start_date, end_date)
    dk_api_responses = [format_api_response(response) for response in dk_api_responses_raw]
    if len(dk_api_responses) == 0:
        print("No data found LLM will response on it's own")
        dk_api_responses = ["Sorry, I was unable to find suitable results."]
    else:
        print(f"dk_api_responses: {dk_api_responses}")

    tool_responses = format_results(dk_api_responses_raw)
    append_to_conversation({"role": "assistant", "tool_calls": api_response.response_tool_data})
    append_to_conversation(
        {"role": "tool", "tool_call_id": api_response.response_tool_id, "content": "\n\n".join(dk_api_responses)})
    print(ai_conversation)
    create_response_from_tool_data(tool_responses)


def create_response_from_tool_data(tool_responses):
    api_response = llm.collect_user_data(ai_conversation)
    if api_response.response_type == LLMResponseType.TEXT:
        llm_answer = api_response.response_text.replace("**", "")
        answer_parts = re.split(r'\r?\n\s*\n', llm_answer)
        print(f"answer_parts: {answer_parts}")
        selection_names = get_cleaned_selection(answer_parts[1:-1])
        print(f"selection names: {selection_names}")
        print(f"tool names: {[response['Title'] for response in tool_responses]}")
        selected_responses = get_selection(selection_names, tool_responses)

        data = dict()
        data["role"] = "assistant"
        data["response_header"] = answer_parts[0]
        data["response_footer"] = answer_parts[len(answer_parts) - 1]
        data["response_data"] = selected_responses
        print(f"final tool response: {data}")
        ai_conversation.append({'role': "assistant", 'content': llm_answer})
        view_conversation.append(data)


def get_cleaned_selection(answer_parts: list[str]) -> list[str]:
    names = list[str]()
    for answer in answer_parts:
        name = answer.split('\n')[0].strip()
        if name[0].isdigit():
            name = name[1:]
        if name[0] == ".":
            name = name[1:]

        names.append(name.strip().lower())

    return names


def get_selection(names: list[str], tool_data: list[dict]) -> list[dict]:
    results = list[dict]()
    for name in names:
        for data in tool_data:
            if data['Title'].strip().lower() == name:
                results.append(data)
                break

    print(f"{len(results)}/{len(names)} name matches found.")
    return results


def format_results(api_responses):
    api_responses = [format_result(response) for response in api_responses]
    print(api_responses)
    return api_responses


def format_result(api_response):
    response = dict()
    response['Id'] = api_response['uuid']
    response['Title'] = clean_text(api_response['name'])
    response['Description'] = clean_text(api_response['description'])
    response['Content'] = clean_text(api_response['body'])
    response['Website'] = api_response['officialWebsite']
    response['Address'] = f"{api_response['address']['block']} {api_response['address']['streetName']}, Singapore {api_response['address']['postalCode']}".strip()
    response['Rating'] = api_response['rating']
    if 'google_data' in api_response:
        image_path = f"static/image_cache/{api_response['google_data']['place_id']}"
        if os.path.exists(image_path):
            response['Image'] = image_path
        else:
            # random fallback image :)
            response['Image'] = f"static/image_cache/ChIJzXNvOzcY2jERZ6JJC0ab_qg"
    else:
        response['Image'] = f"static/image_cache/ChIJzXNvOzcY2jERZ6JJC0ab_qg"

    response['Price'] = '999'
    return response


def clean_text(text):
    text = text.replace("\n", " ")
    regex = r"<.*?>"
    text = re.sub(regex, "", text)
    regex = r"[^\x00-\x7F]"
    return re.sub(regex, "", text)


@app.route("/", methods=["GET", "POST"])
def handle_query_other():
    if request.method == "POST":
        user_query = request.form["user_input"]
        append_to_conversation({"role": "user", "content": user_query})
        collect_data_and_respond()

    return render_template("index.html", conversations=view_conversation)


@app.route("/reset", methods=["GET"])
def handle_reset():
    global ai_conversation
    global view_conversation
    ai_conversation = []
    view_conversation = []

    return render_template("index.html", conversations=view_conversation)


if __name__ == "__main__":
    app.run()
