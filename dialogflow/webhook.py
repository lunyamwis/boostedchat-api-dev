import os
import sys

import requests
import uvicorn
from fastapi import FastAPI, Request

app = FastAPI()

prompts = {
    "NA": """
    Respond to the received DM from a US-based barber that is an answer to the question
    “I was wondering what’s the gnarliest part of your barber gig?". The response needs
    to be a short DM message in a way that sounds natural, confirms that the barber was
    understood, and that you’re amazed that the barber is able to handle situations like
    that. make sure to use a tone of voice in line with those characteristics: "We’re
    revolutionizing the way people make appointments. Barbers and stylists are
    frustrated from wasting too much time managing their books when they could be
    focusing on their craft. Booksy offers a platform for them to streamline business
    management. Both a reliable receptionist and a trustworthy business partner,
    Booksy helps merchants grow and gives them time to master their skills. CONVERSATIONAL
    We are a business partner and friendly neighbor recommending a service or business. Our
    voice needs to match our attitude. Being corporate is too rigid, and can be alienating.
    Speaking casually and candidly allows customers to trust us. ENCOURAGING Our customers
    and merchants dream of fulfilling their full personal potential, and Booksy gives them
    the tools to accomplish that. GENUINE Booksy makes a promise to its customers. We’re
    adding a new meaning to their lives by redefining what it means to manage a business.
    How? By being accurate, honest, transparent, and receptive to customer feedback."
"""
}


convo = []


@app.post("/api/v1/dialogflow")
async def webhook(request: Request):
    try:
        req = await request.json()
        # print('request data', req)
        # fulfillmentText = "you said"
        query_result = req.get("queryResult")
        query = query_result.get("queryText")

        if query_result.get("action") == "input.unknown":
            convo.append("DM:" + query)
            convo.append(prompts.get("NA"))
            prompt = ("\n").join(convo)

            # print('prompt so far', convo)
            response = query_gpt(prompt)

            # print('gpt resp', response)
            result = response.get("choices")[0].get("text")
            result = result.strip("\n")
            # print('result', result)
            convo.append(result)
            print("convo so far", ("\n").join(convo))

            return {"fulfillmentText": result, "source": "webhookdata"}

        # if query_result.get('action') == 'welcome':
        #   print('prompt initialized')
        #   # convo = []

    except Exception as e:
        print("error", e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print("oops", exc_type, fname, exc_tb.tb_lineno)
        return 400


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
    print("time elapsed", res.elapsed.total_seconds())
    # print('\nmodel API response', str(res.json()))
    return res.json()


@app.get("/")
def hello(request: Request):
    print("server is live")
    return {200: "API Runnings"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
