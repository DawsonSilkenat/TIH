from api_endpoint_functions.get_dataset_names import get_datasets
from keywords import get_query_keywords
from api_endpoint_functions.query_multiple_datasets import multiple_datasets_by_keywords
from api_endpoint_functions.format_api_response import format_api_response

from possible_actions.collect_user_data import collect_user_data
from llm_functions import LLMResponseType, LLMResponse
from flask import Flask, render_template, request
import json

# Creating the app and loading api keys 
app = Flask(__name__)
with open("api_keys.json", "r") as file:
    keys = json.load(file)
    tih_api_key = keys["TIH"]

# For now I am just going to store the conversation. This should be replaced eventually, but good enough for poc
ai_conversation = []
view_conversation = []


def append_to_conversation(data : dict):
    ai_conversation.append(data)
    if data['role'] != 'tool' and 'content' in data:
        view_conversation.append(data)


def collect_data_and_respond():
    llm_answer = None
    api_response = collect_user_data(ai_conversation)
    print(f"api_response: {api_response}")
    if api_response.response_type == LLMResponseType.TEXT:
        llm_answer = api_response.response_text
        append_to_conversation({"role": "assistant", "content": llm_answer})
    else:
        datasets = get_datasets(ai_conversation, tih_api_key)
        print(f"datasets: {datasets}")
        keywords = get_query_keywords(ai_conversation)
        print(f"keywords: {keywords}")
        dk_api_responses = multiple_datasets_by_keywords(ai_conversation, datasets, tih_api_key, keywords, 25)
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

    return render_template("demo_page.html", conversations=view_conversation)
    

if __name__ == "__main__":
    app.run()
