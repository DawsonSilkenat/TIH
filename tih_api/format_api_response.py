import re

def format_api_response(api_response: dict[str, any]) -> str:
    """Transforms the dictionary returned by the api into a string which can be processed by the llm

    Args:
        api_response (dict[str, any]): The list of results from the API

    Returns:
        str: A string formatted to be interpretted by the llm
    """
    
    # For now we are only considering the name, description, and body for each response. 
    name = api_response["name"]
    description = api_response["description"]
    body = api_response["body"]
    if float(api_response['rating']) > 1.0:
        rating = f"Rating: {api_response['rating']}"
    else:
        rating = ""

    if 'officialWebsite' in api_response:
        website = f"Website: {api_response['officialWebsite']}"
    else:
        website = ""

    address = f"Address: {api_response['address']['block']} {api_response['address']['streetName']}, Singapore {api_response['address']['postalCode']}"
    #TODO add opening hours


    # Some responses contain newlines to format more nicely for a human reader. Remove these as it may lead to confusion to a machine reader, especially since we are using newlines to distinguish between name, description and body.
    name = name.replace("\n", " ")
    description = description.replace("\n", " ")
    body = body.replace("\n", " ")
    
    # Some responses contain html, which doesn't add anything to the text and makes the result more difficult to read for debugging
    regex = r"<.*?>"
    
    name = re.sub(regex, "", name)
    description = re.sub(regex, "", description)
    body = re.sub(regex, "", body)
    
    
    # Regular expression to match any character outside the ASCII range
    # We remove such characters as they are unlikely to appear frequently, if at all, in llm training
    # TODO consider how I can exclude currency codes from this
    regex = r"[^\x00-\x7F]"
    
    name = re.sub(regex, "", name)
    description = re.sub(regex, "", description)
    body = re.sub(regex, "", body)
    
    return f"{name}\n{description}\n{body}\n{website}\n{address}\n{rating}"