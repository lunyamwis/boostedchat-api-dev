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
