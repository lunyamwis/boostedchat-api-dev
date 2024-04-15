from django.conf import settings
import requests
import json

class ExceptionHandler(object):

    def __init__(self,code_to_handle) -> None:
        self.code_to_handle = code_to_handle

    def handle_401(self,data):
        response = requests.post(settings.MQTT_BASE_URL + "/login", data=json.dumps(data))
        if response.status_code == 200:
            return True
        else:
            return False


    def take_action(self, *args, **kwargs):
        getattr(self, f"handle_{self.code_to_handle}")(*args, **kwargs)

        




