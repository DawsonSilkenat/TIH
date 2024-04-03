from openai import OpenAI
import json

with open("api_keys.json", "r") as file:
    keys = json.load(file)
    openAI_api_key = keys["OpenAI"]
client = OpenAI(api_key=openAI_api_key)

def generate_llm_response(user_prompt: str, response_start: str=None, system_prompt: str=None) -> str:
    messages = []
    
    if system_prompt is not None:
        messages.append({"role": "system", "content": system_prompt})
        
    messages.append({"role": "user", "content": user_prompt})
    
    if response_start is not None:
        messages.append({"role": "assistant", "content": response_start})
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", 
        messages= messages
    )
    
    return response.choices[0].message.content