import random


def get_random_compliment(compliments: dict, compliment_type: str):
    list_compliments = list(compliments)
    _, compliment = random.choice(list_compliments)
    return compliment[compliment_type]
