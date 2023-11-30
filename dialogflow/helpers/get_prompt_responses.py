import re
import os
import json
import requests
from instagram.helpers.llm import query_gpt

def get_status_number(val, pattern=r"\d+"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return int(list_of_values[0])


def get_if_confirmed_problem(val, pattern=r"`([^`]+)`"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return str(list_of_values[0])


def get_if_asked_first_question(val, pattern=r"`([^`]+)`"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return str(list_of_values[0])


def get_gpt_response(account):
    payload = {
        "prompt_index": account.index,
        "company_index": os.getenv("COMPANY_INDEX"),
    }
    url = os.getenv("SCRIPTING_URL")
    response = requests.post(url, data=payload)
    prompt = response.get("prompt")
    steps = int(response.get("steps"))
    response = query_gpt(prompt)

    result = json.loads(response.get("choices")[0].get("message").get("content"))
    completed = int(result.get('completed'))
    if completed and account.index <= steps:
        account.index = account.index + 1
        account.save()
    return result