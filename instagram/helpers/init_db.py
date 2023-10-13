import os
from pathlib import Path

from django.core.files import File

from authentication.models import User
from instagram.models import Account, OutSourced, StatusCheck
from sales_rep.models import SalesRep
from settings.models import AutomationSheet, Industry


def init_status_check():
    # stage 1
    sent_first_compliment = StatusCheck()
    sent_first_compliment.stage = 1
    sent_first_compliment.name = "sent_first_compliment"
    sent_first_compliment.save()

    sent_compliment = StatusCheck()
    sent_compliment.stage = 1
    sent_compliment.name = "sent_compliment"
    sent_compliment.save()

    # stage 2
    sent_first_question = StatusCheck()
    sent_first_question.stage = 2
    sent_first_question.name = "sent_first_question"
    sent_first_question.save()

    confirmed_problem = StatusCheck()
    confirmed_problem.stage = 2
    confirmed_problem.name = "confirmed_problem"
    confirmed_problem.save()

    overcome_objections = StatusCheck()
    overcome_objections.stage = 2
    overcome_objections.name = "overcome_objections"
    overcome_objections.save()

    # stage 3
    overcome = StatusCheck()
    overcome.stage = 3
    overcome.name = "overcome"
    overcome.save()

    deferred = StatusCheck()
    deferred.stage = 3
    deferred.name = "deferred"
    deferred.save()

    # stage 4
    activation = StatusCheck()
    activation.stage = 4
    activation.name = "activation"
    activation.save()


def init_industry():
    industry = Industry()
    industry.name = "Beauty"
    industry.save()


def init_automation_sheet():
    automation_sheet = AutomationSheet()
    automation_sheet.industry = Industry.objects.last()
    automation_sheet.name = "Booksy automation sheet"
    automation_sheet.company = "Booksy"
    automation_sheet.language = "en"
    salesrep = SalesRep()
    salesrep.ig_username = os.getenv("IG_USERNAME")
    salesrep.ig_password = os.getenv("IG_PASSWORD")
    salesrep.user = User.objects.last()
    salesrep.save()
    automation_sheet.salesrep = SalesRep.objects.last()
    path = Path("media/Booksy_Dialogflow_Automations.xlsx")

    with path.open(mode="rb") as f:
        automation_sheet.file = File(f, name=path.name)
        automation_sheet.save()


def init_outsourced():
    data = """
    {"calendar_availability": "Empty Calendar", "booking_system": "StyleSeat", "sm_activity": "SM Not Active", "book_button": "YES", "reviews": [{"reviews": "5.0 (535 Reviews)", "clientPhotosNo": "Get $50", "review_text": "”It was great to meet Paul, who gonna be my new barber, beard stylist. This guy and the whole place seemed chill and relaxing. Great service and attention to detail. Solid place to go to. I’ll be back, no doubt.“", "aboutClientAdjectives": "ATTENTIVE\nON TIME\nPROFESSIONAL", "aboutClientLocation": "CLEAN\nEASY PARKING", "reviewerNameAndDate": "JEFF T.\nFeb 25, 2023", "reviewServiceName": "Beard Line-up | Sculpting"}, {"reviews": "5.0 (535 Reviews)", "clientPhotosNo": "Get $50", "review_text": "”It was great to meet Paul, who gonna be my new barber, beard stylist. This guy and the whole place seemed chill and relaxing. Great service and attention to detail. Solid place to go to. I’ll be back, no doubt.“", "aboutClientAdjectives": "ATTENTIVE\nON TIME\nPROFESSIONAL", "aboutClientLocation": "CLEAN\nEASY PARKING", "reviewerNameAndDate": "JEFF T.\nFeb 25, 2023", "reviewServiceName": "Beard Line-up | Sculpting"}]}
    """
    source = "styleseat"
    outsourced = OutSourced()
    outsourced.source = source
    outsourced.results = data
    account = Account()
    account.igname = "psychologistswithoutborders"
    account.save()
    outsourced.account = account
    outsourced.save()


def init_db():
    init_status_check()
    init_industry()
    init_automation_sheet()
    init_outsourced()
