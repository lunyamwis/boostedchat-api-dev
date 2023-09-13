import logging
import os

import requests


def query_gpt(prompt):
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

    res = requests.post("https://api.openai.com/v1/completions", json=body, headers=header)
    logging.warn(str(["time elapsed", res.elapsed.total_seconds()]))
    # logging.warn('\nmodel API response', str(res.json()))
    return res.json()
