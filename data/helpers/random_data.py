import random

import pandas as pd

from settings.models import AutomationSheet


def get_random_compliment(salesrep: str, compliment_type: str):
    sheet = AutomationSheet.objects.filter(salesrep=salesrep)
    compliment = None
    if sheet.exists():
        company = sheet.last()
        df = pd.read_excel(company.file.path, sheet_name="compliments")
        compliment = random.choice(df[compliment_type])
    return compliment


def get_follow_up_messages(salesrep, day: str):
    sheet = AutomationSheet.objects.filter(salesrep=salesrep)
    day_value = None
    if sheet.exists():
        company = sheet.last()
        df = pd.read_excel(company.file.path, sheet_name="activation")
        day_value = df[day].iloc[0]
    return day_value


def get_problem(salesrep):
    pass


def get_solution(salesrep):
    pass


def get_objection_response(salesrep):
    pass
