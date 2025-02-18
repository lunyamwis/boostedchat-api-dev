import requests
import os
CLICK_UP_BASE_URL = os.environ.get('CLICK_UP_VIEW_API_URL')
CLICK_UP_AUTH = os.environ.get('CLICK_UP_DENN_AUTH')
VIEW_ID = os.environ.get('CLICK_UP_TECH_NOTIFICATIONS_VIEW_ID')

def notify_click_up_tech_notifications(comment_text,notify_all):
  url = f"{CLICK_UP_BASE_URL}/{VIEW_ID}/comment"

  payload = {
      "notify_all": notify_all,
      "comment_text": comment_text
  }
  headers = {
      "accept": "application/json",
      "content-type": "application/json",
      "Authorization": CLICK_UP_AUTH
  }

  response = requests.post(url, json=payload, headers=headers)

  print(response.text)