import os

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response


def query_gpt(prompt):
    api_url = f"{settings.OPENAI_BASE_URL}/completions"
    body = {
        "model": "text-davinci-003",
        "prompt": prompt,
        "max_tokens": 150,
        "temperature": 0.7,
        "top_p": 1,
        "n": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0.6,
    }
    header = {"Authorization": "Bearer " + os.getenv("OPENAI_API_KEY")}

    try:
        res = requests.post(api_url, json=body, headers=header)
        return res.json()
    except requests.RequestException as exc:
        error_message = str(exc)  # Convert the exception to a string
        return Response({"error": error_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
