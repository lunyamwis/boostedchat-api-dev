# import requests
# import os
# CLICK_UP_BASE_URL = os.environ.get('CLICK_UP_BASE_API_URL')
# CLICK_UP_AUTH = os.environ.get('CLICK_UP_DENN_AUTH')
# VIEW_ID = os.environ.get('CLICK_UP_TECH_NOTIFICATIONS_VIEW_ID')
# API_BUG_LIST_ID = os.environ.get('CLICK_UP_API_BUG_LIST_ID')

# def notify_click_up_tech_notifications(comment_text,notify_all):
#   url = f"{CLICK_UP_BASE_URL}/view/{VIEW_ID}/comment"

#   payload = {
#       "notify_all": notify_all,
#       "comment_text": comment_text
#   }
#   headers = {
#       "accept": "application/json",
#       "content-type": "application/json",
#       "Authorization": CLICK_UP_AUTH
#   }

#   response = requests.post(url, json=payload, headers=headers)

#   print(response.text)
  
  
# def create_click_up_task(name, description):
#   url = f"{CLICK_UP_BASE_URL}/list/{API_BUG_LIST_ID}/task"
  

#   payload = {
#       "name": name,
#       "description": description,
#       "notify_all": True
#   }
#   headers = {
#       "accept": "application/json",
#       "content-type": "application/json",
#       "Authorization": "pk_88791014_47ABWL7MICYUNJH0TFOIHW11NLSVWJ6Y"
#   }

#   response = requests.post(url, json=payload, headers=headers)

#   print(response.text)


import requests
import os

CLICK_UP_BASE_URL = os.environ.get('CLICK_UP_BASE_API_URL')
CLICK_UP_AUTH = os.environ.get('CLICK_UP_DENN_AUTH')
VIEW_ID = os.environ.get('CLICK_UP_TECH_NOTIFICATIONS_VIEW_ID')
API_BUG_LIST_ID = os.environ.get('CLICK_UP_API_BUG_LIST_ID')

if not all([CLICK_UP_BASE_URL, CLICK_UP_AUTH, VIEW_ID, API_BUG_LIST_ID]):
    raise EnvironmentError("One or more ClickUp environment variables are missing.")

def click_up_post_request(endpoint, payload):
    """Reusable function to make POST requests to ClickUp API."""
    url = f"{CLICK_UP_BASE_URL}/{endpoint}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": CLICK_UP_AUTH
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request to ClickUp API: {e}")
        return None

def notify_click_up_tech_notifications(comment_text, notify_all=True):
    """Sends a comment notification to the Tech Notifications view in ClickUp."""
    payload = {
        "notify_all": notify_all,
        "comment_text": comment_text
    }
    endpoint = f"view/{VIEW_ID}/comment"
    response = click_up_post_request(endpoint, payload)
    
    if response:
        print("Notification sent successfully:", response)
    else:
        print("Failed to send notification.")

def create_click_up_task(name, description, notify_all=False):
    """Creates a new task in the ClickUp API Bug List."""
    payload = {
        "name": name,
        "description": description,
        "notify_all": notify_all
    }
    endpoint = f"list/{API_BUG_LIST_ID}/task"
    response = click_up_post_request(endpoint, payload)
    
    if response:
        print("Task created successfully:", response)
    else:
        print("Failed to create task.")
