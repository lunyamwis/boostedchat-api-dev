import datetime
import json
import logging
import time
import random

import requests
from celery import shared_task
from django.conf import settings
from django_celery_beat.models import PeriodicTask
from django.shortcuts import get_object_or_404

from instagram.models import Account, Message, OutSourced, StatusCheck, Thread
from sales_rep.models import SalesRep
from dialogflow.helpers.get_prompt_responses import get_gpt_response

from .helpers.format_username import format_full_name
from outreaches.utils import process_reschedule_single_task, ig_thread_exists, not_in_interval ## move
from .utils import get_account, tasks_by_sales_rep
from outreaches.models import OutreachErrorLog
from tabulate import tabulate # for print_logs
from urllib.parse import urlparse
import socket

false = False

def print_logs():
    logs = OutreachErrorLog.objects.all().order_by('-created_at')[:30]  # Assuming OutreachErrorLog is a Django model
    headers = ["Code", "Account", "Sales Rep", "Error Message", "Error Type", "Created At", "Log Level"]
    data = []

    ## print logs
    

    for log in logs:
        sales_rep_username = log.sales_rep.ig_username if log.sales_rep else ""
        data.append([log.code, log.account, sales_rep_username, log.error_message, log.error_type, log.created_at, log.log_level])

    print(tabulate(data, headers=headers, tablefmt="pretty"))

def sales_rep_is_logged_in(account, salesrep):
    igname =  account_has_sales_rep(account)
    data = {
        "igname": igname
    }
    json_data = json.dumps(data)
    response = requests.post(settings.MQTT_BASE_URL + "/accounts/isloggedin", data=json_data, headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        account_list = None
        try:
            account_list = response.json()
        except ValueError:
            outreachErrorLogger(account, salesrep, "Wrong response data. Not JSON", 422, "WARNING", "MQTT", False)
            return False
            # handle error and thoww
        
        if igname in account_list:
            print(f"print is returning....{account_list[igname]}")
            return account_list[igname]
        else:
            outreachErrorLogger(account, salesrep, "Wrong Json data", 422, "WARNING", "MQTT", False)
        return False
    return False

def sales_rep_is_available(account):
    salesrep = account.salesrep_set.first()
    return salesrep.available

def account_has_sales_rep(account):
    salesrep = account.salesrep_set.first()
    if salesrep is not None:
        return salesrep.ig_username
    else:
        return False

def reschedule_last_enabled(salesrep):
    tasks = tasks_by_sales_rep("instagram.tasks.send_first_compliment", salesrep, "enabled", -1, 1, True)
    # task = PeriodicTask.objects.filter(task="instagram.tasks.send_first_compliment", enabled=True).order_by('start_time').last()
    task = tasks[0]
    if task:
        current_time = datetime.datetime.now()
        task_time = current_time + datetime.timedelta(minutes=1)  # Add 1 minute to the current time
        start_hour = task_time.hour
        start_minute = task_time.minute
        process_reschedule_single_task("instagram.tasks.send_first_compliment", task.name, start_hour, start_minute, 48*3)
    else:
        print ('No more enabled tasks found')
    
def outreachErrorLogger(account, sales_rep, error_message, err_code, log_level, error_type, repeat = False):
    #save
    error_log_instance =  OutreachErrorLog()
    error_log_instance.save_log(err_code, error_message, error_type, log_level, account, sales_rep)
    # react
    if repeat and sales_rep:
        reschedule_last_enabled(sales_rep.ig_username)
    if log_level == "WARNING":
        pass
    else: # not action to be taken
        raise Exception(error_message) # ERROR will break execution after rescheduling if repeat is True

def handleMqTTErrors(account, sales_rep, status_code, status_message, numTries, repeat):
    repeatLocal = False # to repeat within calling func without resheduling new. Valid only for authcodes
    error_type = "unknown"  # Default error type

    auth_codes = [401, 403]
    our_errors = [400]

    if status_code in auth_codes:
        error_type = "Sales Rep"
    if status_code in [500]:
        error_type = "Instagram"
    if status_code in our_errors:
        error_type = "MQTT"
    ## 400, others

    log_level = "WARNING" # default
    if status_code in auth_codes and numTries == 1: # first trial of login, enable repeat
        if logout_and_login(account, sales_rep):
            repeatLocal = True
    if status_code in auth_codes and numTries > 1:
        log_level = "ERROR"

    if status_code in auth_codes:
        repeat = False # it will repeat locally using repeatLocal
    try:
        outreachErrorLogger(account, sales_rep, status_message, status_code, log_level, error_type, repeat)
    except Exception as e:
        pass

    # if status_code not in auth_codes and repeat: # by default repeat is true. But we may set it to false for single action trials
    #     reschedule_last_enabled(sales_rep.ig_username)  #### this should be handled by outreachErrorLogger
    
    return repeatLocal
    

def logout(igname):
    data = {
        "igname": igname
    }
    # Convert the data to JSON format
    json_data = json.dumps(data)
    response = requests.post(settings.MQTT_BASE_URL + "/accounts/logout", data=json_data, headers={"Content-Type": "application/json"})
    # Check the response
    if response.status_code == 200:
        print("Logout successful")
    else:
        print("Logout failed:", response.text)

def login(account, salesrep):
    igname = salesrep.ig_username
    data = {
        "igname": igname
    }
    # Convert the data to JSON format
    json_data = json.dumps(data)
    response = requests.post(settings.MQTT_BASE_URL + "/accounts/login", data=json_data, headers={"Content-Type": "application/json"})
    # Check the response
    if response.status_code == 200:
        print("login successful")
        return True
    else:
        print("login failed:", response.text, response.status_code)
        outreachErrorLogger(account, salesrep, response.text, response.status_code, "ERROR", "Account")
        
        #  check: we ill need to handle challenges here
        return False


def logout_and_login(account, salesrep):
    igname = salesrep.ig_username
    logout(igname)
    if not login(account, salesrep):
        return False
    time.sleep(20)
    return True
    # handle response from these...
    # Error handler for this one
def isMQTTUP():
    parsed_url = urlparse(settings.MQTT_BASE_URL)

    # Get the host and port from the parsed URL
    host = parsed_url.hostname
    scheme = parsed_url.scheme

    # Map the scheme to the default port
    default_ports = {'http': 80, 'https': 443}
    port = parsed_url.port or default_ports.get(scheme.lower(), None)

    print(f"Host: {host}")
    print(f"Port: {port}")
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)  # 5 seconds timeout
        s.connect((host, port))
        
        # Connection successful
        print(f"Microservice running on port {port} is available.")
        return True
        
    except Exception as e:
        # Connection failed or timed out
        print(f"Microservice running on port {port} is not available: {e}")
        return False
        
    finally:
        # Close the socket
        s.close()
def user_exists_in_IG(account, salesrep):
    data = {"username_from": salesrep.ig_username, "username_to": account.igname}
    response = requests.post(settings.MQTT_BASE_URL + "/checkIfUserExists", data=json.dumps(data))
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        return False
    else:
        raise Exception(f"Unexpected status code: {response.status_code}")

def delete_first_compliment_task(account):
    try:
        PeriodicTask.objects.get(name=f"SendFirstCompliment-{account.igname}").delete()
    except Exception as error:
        logging.warning(error)


def like_and_comment(media_id, media_comment, salesrep, account):
    like_comment = False
    datasets = []
    dataset = {
        "mediaIds": media_id,
        "username_from": salesrep.ig_username
    }
    datasets.append(dataset)
    response =  requests.post(settings.MQTT_BASE_URL + "/like", data=json.dumps(datasets))
    datasets = []
    if response.status_code == 200:
        time.sleep(105) # we break for 1 minute 45 seconds and then comment
        dataset = {
            "mediaId": media_id,
            "comment": media_comment,
            "username_from": salesrep.ig_username
        }
        datasets.append(dataset)
        response =  requests.post(settings.MQTT_BASE_URL + "/comment", data=json.dumps(datasets))
        if response.status_code == 200:
            like_comment = True
            

            print(f"************* {account.igname} media has been liked and commented ****************" )
        else:
            outreachErrorLogger(account, salesrep, response.text, response.status_code, "WARNING", "Commenting", False) # reshedule_next
        
    else:
        outreachErrorLogger(account, salesrep, response.text, response.status_code, "WARNING", "Liking", False) # reshedule_next
        print(f"************* {account.igname} media has not been liked and commented ****************" )
    return like_comment


    

@shared_task()
def send_first_compliment(username, repeat=True):
    # check if now is within working hours
    # if not_in_interval():
    #     err_str = f"{username} scheduled at wrong time"
    #     outreachErrorLogger(None, None, err_str, 422, "ERROR", "Time", False) # we can not do anything about the time. Do not reschedule
    
    numTries = 0
    print(username)
    thread_obj = None
    account = get_account(username)

    if account is None:
        err_str = f"{username} account does not exist"
        outreachErrorLogger(None, None, err_str, 404, "ERROR", "Lead", True) # reshedule_next
        # raise Exception(err_str)

        
    thread_exists = ig_thread_exists(username)
    if thread_exists:
        outreachErrorLogger(account, None, "Already has thread", 422, "ERROR", "Lead", True) # reshedule_next
    # check that account has sales_rep
    check_value = account_has_sales_rep(account)

    if not check_value:
        err_str = f"{username} has no sales rep assigned"
        outreachErrorLogger(account, None, err_str, 404, "ERROR", "Sales Rep", True) # reshedule_next
        # outreachErrorLogger(err_str)
        # raise Exception(err_str)

    
    account_sales_rep_ig_name = check_value
    check_value = sales_rep_is_available(account)
    if not check_value:
        err_str = f"{account_sales_rep_ig_name} sales rep set for {username} is not available"
        outreachErrorLogger(account, None, err_str, 422, "ERROR", "Sales Rep", False) # Nothing to be done. No action on our part can make it available
        # outreachErrorLogger(err_str)
        # raise Exception(f"{account_sales_rep_ig_name} sales rep set for {username} is not available")

    salesrep = account.salesrep_set.first()
    if not isMQTTUP():
        outreachErrorLogger(account, salesrep, "MQTT service unavailable. Not handled", 503, "ERROR", "MQTT", False) # Nothinig to be done. No action on our part can bring it up
    # check if sales_rep is logged_in
    try:
        logged_in = sales_rep_is_logged_in(account, salesrep)
        if not logged_in: # log in will need to be handled differently from the others
            err_str = f"{account_sales_rep_ig_name} sales rep set for {username} is not logged in"
            outreachErrorLogger(account, salesrep, err_str, 403, "WARNING", "Sales Rep IG", False)  # WARNING will not break execution
            if not logout_and_login(account, salesrep): # Nothing to be done. We cannot try logging in constantly
                return # nothing to do. Wait for the account to be logged back in manually.
  
    except Exception as e:
        print(f"An error occurred: {e}") 
        return

    try:
        ig_account_exists = user_exists_in_IG(account, salesrep)
        if not ig_account_exists: # log in will need to be handled differently from the others
            delete_first_compliment_task(account)
            err_str = f"{username} does not exist"
            outreachErrorLogger(account, salesrep, err_str, 404, "ERROR", "Lead", True)  # WARNING will break execution and reschedule another
  
    except Exception as e:
        print(f"An error occurred: {e}")  # probably an auth error
        return
    # check also if available(1)

    # for development: throw this error:
    # raise Exception("...There is something wrong with mqtt...")

    # full_name = "there"
    # print(f'Account: {account}')
    # try:
    #     full_name = format_full_name(account.full_name)
    # except Exception as error:
    #     print(error)
    
    # raise Exception("There is something wrong with mqt----t")
    outsourced_data = OutSourced.objects.filter(account=account)
    
    first_message = get_gpt_response(account)

    media_id = outsourced_data.last().results.get("media_id", "")
    data = {"username_from":salesrep.ig_username,"message": first_message.get('text'), "username_to": account.igname, "mediaId": media_id}
    

    # like and comment
    is_like_and_comment = like_and_comment(media_id=media_id, media_comment=outsourced_data.last().results.get("media_comment", ""),
                     salesrep=salesrep, account=account)
    if is_like_and_comment:
        time.sleep(60) # we break for 1 minute then send message
        print("successfully liked and commented")

    print(f"data=============={data}")
    print(f"data=============={json.dumps(data)}")
    def send(numTries = 0):
        numTries += 1
        response = requests.post(settings.MQTT_BASE_URL + "/send-first-media-message", data=json.dumps(data))
        print(response.status_code)
        if response.status_code == 200:
            sent_compliment_status = StatusCheck.objects.get(name="sent_compliment")
            account.status = sent_compliment_status
            account.save()
            print(f"response============{response}")
            try:

                print(f"json======================{response.json()}")
                returned_data = response.json()

                try:
                    thread_obj, _ = Thread.objects.get_or_create(thread_id=returned_data["thread_id"])
                except Exception as error:
                    print(error)
                    try:
                        thread_obj = Thread.objects.get(thread_id=returned_data["thread_id"])
                    except Exception as error:
                        print(error)
                thread_obj.thread_id = returned_data["thread_id"]
                thread_obj.account = account
                thread_obj.last_message_content = first_message.get('text')
                thread_obj.unread_message_count = 0
                thread_obj.last_message_at = datetime.datetime.fromtimestamp(int(returned_data['timestamp'])/1000000) # use UTC
                thread_obj.save()

                message = Message()
                message.content = first_message.get('text')
                message.sent_by = "Robot"
                message.sent_on = datetime.datetime.fromtimestamp(int(returned_data["timestamp"]) / 1000000)
                message.thread = thread_obj
                message.save()
                try:
                    PeriodicTask.objects.get(name=f"SendFirstCompliment-{account.igname}").delete()
                except Exception as error:
                    try:
                        PeriodicTask.objects.get(name=f"SendFirstCompliment-{account.igname}-workflow").delete()
                    except Exception as error:
                        logging.warning(error)
                    logging.warning(error)
            except Exception as error:
                print(error)
                print("message not saved")

        else:
            # get last account in queue
            # delay 2 minutes
            # send  

            # TODO: Follow the example below so that we can adopt the object oriented paradigm,
            # and increase the team as a result increasing thoroughput
            # study the article below as we continue refactoring the codebase https://refactoring.guru/refactoring/what-is-refactoring

            # exception = ExceptionModel.objects.create(
            #     code = response.status_code,
            #     affected_account = account,
            #     data = {"igname": salesrep.ig_username},
            #     error_message = response.text
            # )
            
            # ExceptionHandler(exception.status_code).take_action(data=exception.data)
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response message: {response.text}")
            # sav
            repeatLocal = handleMqTTErrors(account, salesrep, response.status_code, response.text, numTries, repeat)
            if repeatLocal and numTries <= 1:
                send(numTries)
                # pass
    send()

        # raise Exception("There is something wrong with mqtt")
