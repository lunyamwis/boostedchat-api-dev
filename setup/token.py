import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/dialogflow"]

# Replace with the path to your JSON key file
KEY_FILE = "dialogflow.json"


def acquire_token():
    credentials = None
    token_json = "dialogflow_token.json"
    credentials_json = "dialogflow.json"
    if os.path.exists(token_json):
        credentials = Credentials.from_authorized_user_file(token_json, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_json, SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_json, "w") as token:
            token.write(credentials.to_json())
    return credentials.token
