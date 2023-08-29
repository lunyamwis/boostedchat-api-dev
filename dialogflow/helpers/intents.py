import requests
from django.conf import settings

from setup.token import acquire_token


def detect_intent(project_id, session_id, message, language_code):
    api_url = f"{settings.DIALOGFLOW_BASE_URL}/projects/{project_id}/agent/sessions/{session_id}:detectIntent"
    access_token = acquire_token()  # Replace with your actual access token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "queryInput": {
            "text": {
                "text": message,
                "languageCode": language_code,
            }
        }
    }
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception if response status is not 2xx
        response_data = response.json()
        fulfillment_text = response_data["queryResult"]["fulfillmentText"]
        return fulfillment_text
    except requests.exceptions.RequestException as error:
        error_message = str(error)
        return {"error": error_message}
