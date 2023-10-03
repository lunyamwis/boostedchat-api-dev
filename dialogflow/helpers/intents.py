import requests
from django.conf import settings

from setup.token import acquire_token


def detect_intent(project_id, session_id, message, language_code, account_id):
    api_url = (
        f"{settings.DIALOGFLOW_BASE_URL}agents/75e6b858-16b4-428f-92ed-3b53930144a1/sessions/{session_id}:detectIntent"
    )
    access_token = acquire_token()  # Replace with your actual access token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }
    payload = {
        "queryInput": {
            "languageCode": language_code,
            "text": {
                "text": message
            },
        },
        "queryParams": {
            "payload": {
                "account_id": account_id,
            }
        }
        }
    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an exception if response status is not 2xx
        response_data = response.json()
        print("<<<<Resopins>>>>")
        print(response_data)
        print("<<<<Resopins>>>>")
        fulfillment_text = response_data["queryResult"]["responseMessages"][0].get("text").get("text")
        return fulfillment_text
    except requests.exceptions.RequestException as error:
        error_message = str(error)
        return {"error": error_message}
