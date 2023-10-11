from pathlib import Path
from django.core.files import File
from sales_rep.models import SalesRep
from instagram.models import StatusCheck
from settings.models import Industry, AutomationSheet


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
    automation_sheet.salesrep = SalesRep.objects.last()
    path = Path("media/Booksy_Dialogflow_Automations.xlsx")

    with path.open(mode="rb") as f:
        automation_sheet.file = File(f, name=path.name)
        automation_sheet.save()

def init_db():
    init_status_check()
    init_industry()
    init_automation_sheet()
