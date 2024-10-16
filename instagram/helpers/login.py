import email
import imaplib
import logging
import os
import random
import re
import time
from pathlib import Path

from instagrapi import Client
from instagrapi.mixins.challenge import ChallengeChoice

logger = logging.getLogger()


def change_password_handler(username):
    # Simple way to generate a random string
    chars = list("abcdefghijklmnopqrstuvwxyz1234567890!&£@#")
    password = "".join(random.sample(chars, 8))
    return password


def get_code_from_email(username):
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(os.getenv("CHALLENGE_EMAIL"), os.getenv("CHALLENGE_PASSWORD"))
    mail.select("inbox")
    result, data = mail.search(None, "(UNSEEN)")
    assert result == "OK", "Error1 during get_code_from_email: %s" % result
    ids = data.pop().split()
    for num in reversed(ids):
        mail.store(num, "+FLAGS", "\\Seen")  # mark as read
        result, data = mail.fetch(num, "(RFC822)")
        assert result == "OK", "Error2 during get_code_from_email: %s" % result
        msg = email.message_from_string(data[0][1].decode())
        payloads = msg.get_payload()
        if not isinstance(payloads, list):
            payloads = [msg]
        code = None
        for payload in payloads:
            body = payload.get_payload(decode=True).decode()
            if "<div" not in body:
                continue
            match = re.search(">([^>]*?({u})[^<]*?)<".format(u=username), body)
            if not match:
                continue
            print("Match from email:", match.group(1))
            match = re.search(r">(\d{6})<", body)
            if not match:
                print('Skip this email, "code" not found')
                continue
            code = match.group(1)
            if code:
                return code
    return False


def challenge_code_handler(username, choice):
    if choice == ChallengeChoice.EMAIL:
        return get_code_from_email(username)
    return False


def login_user(username=os.getenv("IG_USERNAME"), password=os.getenv("IG_PASSWORD")):
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """

    cl = Client()
    cl.set_proxy(
        f"https://{os.getenv('PROXY_USERNAME')};country=KE;city=Nairobi:{os.getenv('PROXY_PASSWORD')}@premium.residential.proxyrack.net:10000"
    )
    cl.challenge_code_handler = challenge_code_handler(username, 1)
    cl.delay_range = [1, 3]
    max_attempts = 5
    session_file_path = Path(f"{username}.json")
    if os.path.exists(session_file_path):
        for attempt in range(1, max_attempts + 1):
            session = cl.load_settings(session_file_path)
            if session:
                cl.set_settings(session)
                try:
                    cl.get_timeline_feed()  # Check if the session is valid
                    print("Session is valid, login with session")

                    break
                except Exception as e:
                    old_session = cl.get_settings()
                    cl.set_settings({})
                    cl.set_uuids(old_session["uuids"])
                    print(f"Session is invalid (attempt {attempt}): {e}")
                    if attempt < max_attempts:
                        print(f"Waiting 1 minute before trying again (attempt {attempt})")
                        time.sleep(60)  # Wait for 1 minute
                    else:
                        print("All attempts failed, removing session file and logging in with username and password")
                        os.remove(session_file_path)
                        cl.login(username, password)
                        cl.dump_settings(session_file_path)
                        print("Session saved to file")
    else:
        cl.login(username, password)
        print("Login with username and password")
        cl.dump_settings(session_file_path)
        print("Session saved to file")
    return cl
