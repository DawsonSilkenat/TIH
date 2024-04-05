from api_endpoint_functions.get_dataset_names import get_datasets
from keywords import get_query_keywords
from api_endpoint_functions.query_multiple_datasets import multiple_datasets_by_keywords
from generate_reply import answer_user_query
from flask import Flask, render_template, request
import json

# Creating the app and loading api keys 
app = Flask(__name__)
with open("api_keys.json", "r") as file:
    keys = json.load(file)
    tih_api_key = keys["TIH"]

# For now I am just going to store the conversation. This should be replaced eventually, but good enough for poc
conversation = []

@app.route("/", methods=["GET", "POST"])
def handle_query():
    llm_answer = None
    user_query = None
    
    if request.method == "POST":
        user_query = request.form["user_input"]
        conversation.append({"role": "user", "content": user_query})


        
        datasets = get_datasets(conversation, tih_api_key)
        print(datasets)
        
        keywords = get_query_keywords(conversation)
        print(keywords)
    
        # For now I am using just the Search Multiple Datasets By Keyword endpoint
        # This is the simplest method. I would also like to look at doing each endpoint individually, but not MVP 
        # Concern: Even though this may pull from multiple datasets, I don't think there is any reason to expect it will since the first n results may be from a single dataset
        api_responses = multiple_datasets_by_keywords(conversation, datasets, tih_api_key, keywords, 25)
    
        # Here would be the place to look at deals, augment the information provided to the llm
    
        # Once we have the api responce we need the llm to process the response 
        llm_answer = answer_user_query(conversation, api_responses)
        
        # chatgpt thinks it is writing markdown, so sometimes uses ** to make words bold. This doesn't work, either because it isn't valid html or because flask escapes it
        llm_answer = llm_answer.replace("**", "") 
        
        
        
        
        conversation.append({"role": "assistant", "content": llm_answer})
        
        
    return render_template("demo_page.html", user_query=user_query, llm_answer=llm_answer)
    

if __name__ == "__main__":
    app.run()
