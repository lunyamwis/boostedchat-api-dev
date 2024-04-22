from django.conf import settings
import requests
import json
import time

class ExceptionHandler(object):

    def __init__(self,code_to_handle) -> None:
        self.code_to_handle = code_to_handle

    def handle_401(self,data):
        # logout first
        response = requests.post(settings.MQTT_BASE_URL + "/accounts/logout", data=json.dumps(data), headers={"Content-Type": "application/json"})
        # Check the response
        if response.status_code == 200:
            print("Logout successful")
        else:
            print("Logout failed:", response.text)

        time.sleep(5) # take a 5 second break

        # login
        response = requests.post(settings.MQTT_BASE_URL + "/login", data=json.dumps(data))


        time.sleep(10) # take a 10 second break after logging in so that the user can connect

        if response.status_code == 200:
            return True
        else:
            return False
        

    def handle_403(self,data):
        # logout first
        response = requests.post(settings.MQTT_BASE_URL + "/accounts/logout", data=json.dumps(data), headers={"Content-Type": "application/json"})
        # Check the response
        if response.status_code == 200:
            print("Logout successful")
        else:
            print("Logout failed:", response.text)

        time.sleep(5) # take a 5 second break

        # login
        response = requests.post(settings.MQTT_BASE_URL + "/login", data=json.dumps(data))

        time.sleep(10) # take a 10 second break after logging in so that the user can connect


        if response.status_code == 200:
            return True
        else:
            return False


    def take_action(self, *args, **kwargs):
        getattr(self, f"handle_{self.code_to_handle}")(*args, **kwargs)

        




