# from apscheduler.schedulers.background import BackgroundScheduler
# from datetime import datetime, timedelta
# import time

# # Define a function to be scheduled
# def send_first_compliment(user_id, compliment):
#     print(f"Sending compliment '{compliment}' to user with ID {user_id} at {datetime.now()}.")

# # Create an instance of BackgroundScheduler
# scheduler = BackgroundScheduler()

# # Schedule the task to run at a specific time
# run_time = datetime.now() + timedelta(minutes=4)  # Set your desired date and time here
# scheduler.add_job(send_first_compliment, 'date', args=[123, "You're doing great!"], run_date=run_time)

# # Start the scheduler
# scheduler.start()

# try:
#     # Keep the script running
#     while True:
#         time.sleep(1)
# except (KeyboardInterrupt, SystemExit):
#     # Shut down the scheduler when exiting the app
#     scheduler.shutdown()

import time
from datetime import datetime, timedelta

def my_scheduled_task():
    print(f"Task executed at: {datetime.now()}")

def run_scheduler(target_time):
    """
    A custom scheduler to execute a task at the specified target time.
    
    :param target_time: The datetime object specifying when to run the task.
    """
    print(f"Scheduler started. Current time: {datetime.now()}, Target time: {target_time}")
    
    while True:
        now = datetime.now()
        if now >= target_time:
            my_scheduled_task()
            break  # Exit the loop after running the task
        time.sleep(1)  # Sleep for 1 second to avoid busy-waiting

if __name__ == "__main__":
    # Set the target time to 4 minutes from now
    current_time = datetime.now()
    target_time = current_time + timedelta(minutes=2)
    
    # Run the scheduler
    run_scheduler(target_time)
    run_scheduler(target_time+timedelta(minutes=1))
