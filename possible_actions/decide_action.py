import llm_functions
from possible_actions.provide_answer import answer_user_query
from possible_actions.ask_followup import get_more_information

def decide_action(conversation: list[dict[str, str]], api_responses: list[str]):
    
    system_prompt = "\n".join((
        "Your are a chatbot helping users with their visits to Singapore.",
        "Your current task is to make a decision about the next action you will take in this converation.",
        "You may either attempt to answer the user's query or ask a follow up question clarify the user's interests.",
        "In either case, the following information will be available for that next step."
        "attractions:",
        "\n\n".join(api_responses),
        "",
        "If you believe you have enough information to provide a personalised reply, say 'answer'",
        "If you would like to ask a question to better understand the user's needs, say 'question'",
        "Your response should be either 'answer' or 'question' and nothing else",
        "Do not attempt to answer the user's question at this stage."
    ))
    
    
    next_action = llm_functions.generate_llm_response(conversation, response_start="My next action should be:", system_prompt=system_prompt)
    print(next_action)
    
    if "answer" in next_action.lower():
        return answer_user_query(conversation, api_responses)
    elif "question" in next_action.lower():
        return get_more_information(conversation, api_responses)
    else:
        raise RuntimeError("Not a valid action")
    
    