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


def get_gpt_response(account, message, thread_id=None):
   
    outsourced = None
    try:
        outsourced_object = OutSourced.objects.filter(account__igname=account.igname).first()
        outsourced = json.dumps(outsourced_object.results)
    except Exception as error:
        print(error)

    url = os.getenv("SCRIPTING_URL") + '/getAgent/'
    conversations = get_conversation_so_far(account.thread_set.latest('created_at').thread_id)
    get_agent_payload = {
        "message":message,
        "conversations":conversations if conversations else ""
    }
    agent_response= requests.post(url, data=json.dumps(get_agent_payload),headers = {'Content-Type': 'application/json'})
    agent_json_response = agent_response.json()
    print(agent_json_response)
    # import pdb;pdb.set_trace()
    payload = {
        "department":"Engagement Department",
        "agent_name": agent_json_response.get("agent_name"),
        "agent_task": agent_json_response.get("agent_task"),
        "converstations": conversations if conversations else "",
        "Assigned":{
            "message":message,
            "sales_rep":account.salesrep_set.first().ig_username,
            "influencer_ig_name":account.salesrep_set.last().ig_username,
            "outsourced_info":outsourced_object.results,
            "relevant_information":outsourced_object.results
        }
    }
    print(payload)
    print(message)
    print(url)
    url = os.getenv("SCRIPTING_URL") + '/agentSetup/'
    print(url)
    # import pdb;pdb.set_trace()
    resp = requests.post(url, data=json.dumps(payload),headers = {'Content-Type': 'application/json'})
    response = resp.json()
    print(resp.json())
    result = response.get("result")
    # print(result)
    # import pdb;pdb.set_trace()
    #results = json.loads(result.replace('```json\n','').replace('```',''))['text']
    print(result)
    return result
