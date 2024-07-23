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
    # print(agent_json_response)
    # confirmed_problems = [
    #     "Need for new clients or increased clientele and market visibility",
    #     "Missed opportunities in diversifying revenue streams",
    #     "Inefficient payment processing",
    #     "Missed opportunity to promote your high-potential IG account by posting regularly with social media post creator tools",
    #     "Missed opportunity to enable bookings from platforms (Google, Instagram, Facebook, Booksy which is the biggest beauty marketplace, their Website) where clients discover and book beauty services",
    #     "Not assigning the right priority to engaging the returning, loyal clients",
    #     "Missed opportunity to reengage clients and fill up slower days with time-sensitive promotions",
    #     "Lack of ability to invite back to the chair the clients who stopped booking to build long-term success on returning clients",
    #     "Reviews are not visible across Google, Facebook, IG, and Booksy which is the major beauty marketplace",
    #     "Unclear and high client acquisition costs with Google Ads, Instagram Ads, and others that don't show total marketing cost per new client",
    #     "Missed opportunity to convert current and future IG followers to clients in the chair",
    #     "Need for new clients or increased clientele and market visibility ",
    #     "No-shows and cancellations ruining the bottom line",
    # ]
    
    agent_name = agent_json_response.get("agent_name")
    agent_task = agent_json_response.get("agent_task")


    if account.question_asked and not account.confirmed_problems or account.confirmed_problems == "test" and not account.solution_presented:
        agent_name = "Engagement Persona Influencer Audit Needs Assessment Agent"
        agent_task = "ED_PersonaInfluencerAuditNeedsAssessmentA_BuildMessageT"
    elif account.question_asked and account.confirmed_problems and account.confirmed_problems != "test" and not account.solution_presented:
        agent_name = "Engagement Persona Influencer Audit Solution Presentation Agent"
        agent_task = "ED_PersonaInfluencerAuditSolutionPresentationA_BuildMessageT"
    elif account.question_asked and account.confirmed_problems and account.confirmed_problems != "test" and account.solution_presented:
        agent_name = "Engagement Persona Influencer Audit Closing the Sale Agent"
        agent_task = "ED_PersonaInfluencerAuditClosingTheDealA_BuildMessageT"
                        

    
    print("agent_name:",agent_name,"agent_task:",agent_task)

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
    # Find the index of the opening quote after "text":
    try:
        index = result.find('"question_asked":')
        if index != -1:
            # Extract the value of 'solution_presented'
            question_asked = result[index + 19:].split(',')[0].strip()
            # Find the first digit in the text
            match = re.search(r'\d', question_asked)

            # If a digit is found
            if match:
                # Extract the digit
                first_digit = match.group(0)
                if int(first_digit) == 1:
                    print(f"The first digit found in the text is: {first_digit}")
                    # agent_name = "Engagement Persona Influencer Audit Closing the Sale Agent"
                    # agent_task = "ED_PersonaInfluencerAuditClosingTheDealA_BuildMessageT"
                    
                    account.question_asked = True
                    account.save()
            else:
                print("No digit found in the text.")

        try:
            confirmed_problems_str = result.split('"confirmed_problems": [')[1].split(']')[0]
        except Exception as error:
            try:
                confirmed_problems_str = result.split('"confirmed_problems":')[1].split(']')[0]
            except Exception as error:
                print (error)            
        confirmed_problems = [problem.strip('"') for problem in confirmed_problems_str.split(',')]

        # Iterate over the confirmed problems
        for problem in confirmed_problems:
            # Check if the problem exists in the text
            if problem.lower() in result.lower():
                print(f"Confirmed problem found: {problem}")
                # agent_name = "Engagement Persona Influencer Audit Solution Presentation Agent"
                # agent_task = "ED_PersonaInfluencerAuditSolutionPresentationA_BuildMessageT"
                
                account.confirmed_problems = problem.lower().strip().replace("\"","")
                account.save()
                index = result.find('"solution_presented":')
                if index != -1:
                    # Extract the value of 'solution_presented'
                    solution_presented = result[index + 19:].split(',')[0].strip()
                    # Find the first digit in the text
                    match = re.search(r'\d', solution_presented)

                    # If a digit is found
                    if match:
                        # Extract the digit
                        first_digit = match.group(0)
                        if int(first_digit) == 1:
                            print(f"The first digit found in the text is: {first_digit}")
                            # agent_name = "Engagement Persona Influencer Audit Closing the Sale Agent"
                            # agent_task = "ED_PersonaInfluencerAuditClosingTheDealA_BuildMessageT"
                            
                            account.solution_presented = True
                            account.save()
                    else:
                        print("No digit found in the text.")
                    #print(f"The value of 'solution_presented' is: {solution_presented}")
                else:
                    print("'solution_presented' not found in the text.")
            else:
                print(f"No match found for: {problem}")
    except Exception as err:
        print("There are no confirmed problems")

    print(result)

    # start_index = result.find('"text": "') + len('"text": "')
    
    # # Find the index of the closing quote before the end of the text
    # end_index = result.rfind('"', start_index)
    
    # # Extract the text
    # extracted_text = result[start_index:end_index]
    
    # print(result)
    # import pdb;pdb.set_trace()
    extracted_text = json.loads(result.replace('```json\n','').replace('```',''))['text']
    # extracted_text = extracted_text.replace('\n\n', ' ').replace('\n', ' ')
    print(extracted_text)


    return extracted_text
