import llm_functions


def get_query_keywords(conversation: list[dict[str, str]]) -> list[str]:
    system_prompt = """ Your are supporting with breaking down a conversation that want to get activity recommendations 
    during there vacation. The conversation should be broken down into a few important keywords provided by the user.
    The result should contain a maximum of 10 keywords.
    The keywords must be valid url arguments therefore characters such as / or . are not allowed.
    
    Example Conversation:
    user: I want to visit some music event.
    assistant: What are your music preferences?
    user: I like techno and rock.
    assistant: How long do you stay in singapore?
    user: from 01/03/23 to 20/03/23.
    assistant: Are you visiting singapore alone or in a group?
    user: with my family.
    assistant: how many people and how old are they?
    user: 4 people: 35, 36, 7, 8
    assistant: Therefore it needs to be family friendly?
    user: yes
    
    Example Result: family-friendly, children, music, techno, rock
    
    Conversation: <conversation>.
    Results: 
    """

    simplified_conversation = list()
    for data in conversation:
        simplified_conversation.append(f"{data['role']}: {data['content']}")

    system_prompt = system_prompt.replace("<conversation>", "\n\n".join(simplified_conversation))

    keywords_response = llm_functions.generate_llm_response([], system_prompt=system_prompt).response_text
    
    keywords_response = keywords_response.split(", ")
    
    return keywords_response