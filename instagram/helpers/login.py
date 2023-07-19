import os
import time
from instagrapi import Client
import logging
from pathlib import Path

logger = logging.getLogger()


def login_user():
    """
    Attempts to login to Instagram using either the provided session information
    or the provided username and password.
    """

    cl = Client()
    max_attempts = 5
    session_file_path = Path("session.json")
    if os.path.exists(session_file_path):
        for attempt in range(1, max_attempts + 1):
            cl.load_settings(session_file_path)
            try:
                cl.get_timeline_feed()  # Check if the session is valid
                print("Session is valid, login with session")
                break
            except Exception as e:
                print(f"Session is invalid (attempt {attempt}): {e}")
                if attempt < max_attempts:
                    print(f"Waiting 1 minute before trying again (attempt {attempt})")
                    time.sleep(60)  # Wait for 1 minute
                else:
                    print("All attempts failed, removing session file and logging in with username and password")
                    os.remove(session_file_path)
                    cl.login("darwin_okuku", "DarwinOkuku1*")
                    cl.dump_settings(session_file_path)
                    print("Session saved to file")
    else:
        cl.login("darwin_okuku", "DarwinOkuku1*")
        print("Login with username and password")
        cl.dump_settings(session_file_path)
        print("Session saved to file")
    return cl
