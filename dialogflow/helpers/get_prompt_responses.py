import re
import os
import json
import requests
from instagram.helpers.llm import query_gpt
from urllib.parse import urlparse

def get_status_number(val, pattern=r"\d+"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return int(list_of_values[0])


def get_if_confirmed_problem(val, pattern=r"`([^`]+)`"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return str(list_of_values[0])


def get_if_asked_first_question(val, pattern=r"`([^`]+)`"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return str(list_of_values[0])


def save_gpt_response(result,payload):
    payload.update({
        "dynamic_content": result.get("dynamic_content","")
    })
    url = os.getenv("SCRIPTING_URL") + '/save-response/'
    resp = requests.post(url, data=payload)
    return resp.status_code



def get_gpt_response(account):
    app_url = os.getenv("APP_URL")
    parsed_app_url = urlparse(app_url)
    parsed_app_url_to_split = parsed_app_url.netloc
    subdomains = parsed_app_url_to_split.split('.')
    payload = {
        "prompt_index": account.index,
        "company_name": subdomains[1],
        "product_name": subdomains[2]
    }
    url = os.getenv("SCRIPTING_URL") + '/get-prompt/'
    resp = requests.post(url, data=payload)
    response = resp.json()
    prompt = response.get("prompt")
    steps = int(response.get("steps"))
    response_ = query_gpt(prompt)
    result = json.loads(response_.get("choices")[0].get("message").get("content"))
    completed = int(result.get('completed'))
    if completed and account.index <= steps:
        account.index = account.index + 1
        account.save()
        if result.get("dynamic_content"):
            save_gpt_response(result, payload)
    return result