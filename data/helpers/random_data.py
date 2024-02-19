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


def get_matching_questions(calendar_availability, booking_system, sm_activity, book_button):
    sheet = AutomationSheet.objects.last()
    df = pd.read_excel(sheet.file.path, sheet_name="problems_solutions")
    filtered_df = df[
        (df["calendar_availability"].str.contains(calendar_availability))
        & (df["booking_system"].str.contains(booking_system))
        & (df["sm_activity"].str.contains(sm_activity))
        & (df["book_button"].str.contains(book_button))
    ]

    if len(filtered_df) > 0:
        return {
            "na_question_1": filtered_df["na_question_1"].iloc[0],
            "na_question_2": filtered_df["na_question_2"].iloc[0],
            "na_question_3": filtered_df["na_question_3"].iloc[0],
        }
    else:
        return {"na_question_1": None, "na_question_2": None, "na_question_3": None}


def get_potential_problems(calendar_availability, booking_system, sm_activity, book_button):
    sheet = AutomationSheet.objects.last()
    df = pd.read_excel(sheet.file.path, sheet_name="problems_solutions")
    filtered_df = df[
        (df["calendar_availability"].str.contains(calendar_availability))
        & (df["booking_system"].str.contains(booking_system))
        & (df["sm_activity"].str.contains(sm_activity))
        & (df["book_button"].str.contains(book_button))
    ]

    if len(filtered_df) > 0:
        return {
            "potential_problem_1": filtered_df["potential_problem_1"].iloc[0],
            "potential_problem_2": filtered_df["potential_problem_2"].iloc[0],
            "potential_problem_3": filtered_df["potential_problem_3"].iloc[0],
        }
    else:
        return {"potential_problem_1": None, "potential_problem_2": None, "potential_problem_3": None}


def get_matching_solutions(calendar_availability, booking_system, sm_activity, book_button):
    sheet = AutomationSheet.objects.last()
    df = pd.read_excel(sheet.file.path, sheet_name="problems_solutions")
    filtered_df = df[
        (df["calendar_availability"].str.contains(calendar_availability))
        & (df["booking_system"].str.contains(booking_system))
        & (df["sm_activity"].str.contains(sm_activity))
        & (df["book_button"].str.contains(book_button))
    ]

    if len(filtered_df) > 0:
        return {
            "solution_1": filtered_df["solution_1"].iloc[0],
            "solution_2": filtered_df["solution_2"].iloc[0],
            "solution_3": filtered_df["solution_3"].iloc[0],
        }
    else:
        return {"solution_1": None, "solution_2": None, "solution_3": None}


def get_matching_objection_response(objection):
    sheet = AutomationSheet.objects.last()
    df = pd.read_excel(sheet.file.path, sheet_name="overcoming_objections")
    filtered_df = df[df["objection"].str.contains(objection, case=False, na=False)]

    if len(filtered_df) > 0:
        return filtered_df["response_a"].iloc[0]
    else:
        return None
