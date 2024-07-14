#!/bin/bash

# python3 -m pip install -r requirements.txt # run only once
# python3 -m venv env # run only once
source env/bin/activate
# Execute commands from .env file
source <(sed 's/^/export /' .env)

# Run Django server
python3 manage.py runserver 8001
