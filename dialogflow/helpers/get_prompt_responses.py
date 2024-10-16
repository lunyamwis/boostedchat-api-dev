import re
import os
import json
import requests
from instagram.helpers.llm import query_gpt
from urllib.parse import urlparse
from dialogflow.helpers.conversations import get_conversation_so_far
from instagram.models import OutSourced


def get_status_number(val, pattern=r"\d+"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return int(list_of_values[0])


def get_if_confirmed_problem(val, pattern=r"`([^`]+)`"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return str(list_of_values[0])


def get_if_asked_first_question(val, pattern=r"`([^`]+)`"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return str(list_of_values[0])


def save_gpt_response(result, payload):
    print("===========now============")
    print(result.get("confirmed_problems"))
    print(payload.get("prompt_index"))
    if isinstance(result.get("confirmed_problems"), list):
        payload.update({
            "confirmed_problems": result.get("confirmed_problems")
        })
    else:
        payload.update({
            "confirmed_problems": [result.get("confirmed_problems")]
        })
    url = os.getenv("SCRIPTING_URL") + '/save-response/'
    headers = {'Content-Type': 'application/json'}  # Adjust based on your payload type

    response = requests.post(url, json=payload, headers=headers)

    print(response.request.body)
    return response.status_code


def get_gpt_response(account, thread_id=None):
    app_url = os.getenv("APP_URL")
    parsed_app_url = urlparse(app_url)
    parsed_app_url_to_split = parsed_app_url.netloc
    subdomains = parsed_app_url_to_split.split('.')

    outsourced = None
    try:
        outsourced_object = OutSourced.objects.filter(account__igname=account.igname).first()
        outsourced = json.dumps(outsourced_object.results)
    except Exception as error:
        print(error)

    payload = {
        "prompt_index": account.index,
        "company_name": subdomains[1],
        "product_name": subdomains[2],
        "conversations": get_conversation_so_far(thread_id=thread_id),
        "outsourced": outsourced,
        "checklist": ["book_button", "is_popular", "external_url"],
        "salesrep": account.salesrep_set.last().ig_username
    }
    url = os.getenv("SCRIPTING_URL") + '/get-prompt/'
    resp = requests.post(url, data=payload)
    response = resp.json()
    prompt = response.get("prompt")
    print("Start Prompt")
    print(prompt)
    print("End Prompt")
    steps = int(response.get("steps"))
    print(steps)
    response_ = query_gpt(prompt)
    print("Start response")
    print(response_)
    print("End Response")
    result = json.loads(response_.get("choices")[0].get("message").get("content"))
    completed = int(result.get('completed'))
    if completed:
        if account.index == steps:
            raise Exception("Lead is interested and has been transferred to human takeover")
        elif account.index < steps:
            account.index = account.index + 1
            account.save()

    if "status" in result:
        account.status_param = result.get('status','')
        account.save()
    
    if "human_takeover" in result:
        if result.get('human_takeover') == 1:
            account.assigned_to = 'Human'
            account.save()

    if "referral" in result:
        if result.get("referral"):
            account.referral = result.get("referral",'')
            account.save()

    if "script_score" in result:
        if result.get("script_score"):
            account.script_score = int(result.get("script_score",1))
            account.save()
        
    if "script_version" in result:
        if result.get("script_version"):
            account.script_version = result.get("script_version",'')
            account.save()

    if "confirmed_problems" in result:
        print("these are the confirmed problems in number: ", len(result.get("confirmed_problems")))
        if len(result.get("confirmed_problems")) >= 2:
            print("=========================STET===================")
            print(result.get("confirmed_problems"))

            account.index = account.index + 1
            account.confirmed_problems = result.get("confirmed_problems")
            account.save()
            save_gpt_response(result, payload)
    
   
    return result
