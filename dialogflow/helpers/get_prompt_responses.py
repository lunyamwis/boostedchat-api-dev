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
    confirmed_problems = [
        "Need for new clients or increased clientele and market visibility",
        "Missed opportunities in diversifying revenue streams",
        "Inefficient payment processing",
        "Missed opportunity to promote your high-potential IG account by posting regularly with social media post creator tools",
        "Missed opportunity to enable bookings from platforms (Google, Instagram, Facebook, Booksy which is the biggest beauty marketplace, their Website) where clients discover and book beauty services",
        "Not assigning the right priority to engaging the returning, loyal clients",
        "Missed opportunity to reengage clients and fill up slower days with time-sensitive promotions",
        "Lack of ability to invite back to the chair the clients who stopped booking to build long-term success on returning clients",
        "Reviews are not visible across Google, Facebook, IG, and Booksy which is the major beauty marketplace",
        "Unclear and high client acquisition costs with Google Ads, Instagram Ads, and others that don't show total marketing cost per new client",
        "Missed opportunity to convert current and future IG followers to clients in the chair",
        "Need for new clients or increased clientele and market visibility ",
        "No-shows and cancellations ruining the bottom line",
    ]
    
    agent_name = agent_json_response.get("agent_name")
    agent_task = agent_json_response.get("agent_task")

    for problem in confirmed_problems:
        # Check if the problem exists in the text
        if problem.lower() in conversations:
            print(f"Confirmed problem found: {problem}")
            agent_name = "Engagement Persona Influencer Audit Solution Presentation Agent"
            agent_task = "ED_PersonaInfluencerAuditSolutionPresentationA_BuildMessageT"
        else:
            print(f"No match found for: {problem}")
    # import pdb;pdb.set_trace()
    payload = {
        "department":"Engagement Department",
        "agent_name": agent_name,
        "agent_task": agent_task,
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
