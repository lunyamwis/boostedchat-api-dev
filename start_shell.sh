#!/bin/bash

# Execute commands from .env file
source <(sed 's/^/export /' .env)

# Run Django shell
python3 manage.py shell
