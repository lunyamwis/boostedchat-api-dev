#!/bin/bash

# source /root/.local/share/virtualenvs/brooks-insurance-*/bin/activate

echo "<<<<<<<< Collect Staticfiles>>>>>>>>>"
python3 manage.py collectstatic --noinput


sleep 5
echo "<<<<<<<< Database Setup and Migrations Starts >>>>>>>>>"
# Run database migrations
# python3 manage.py makemigrations
python3 manage.py migrate &

sleep 5
echo "<<<<<<< Initializing the Database >>>>>>>>>>"
echo " "
python manage.py loaddata initialization.yaml
echo " "
echo "<<<<<<<<<<<<<<<<<<<< START Celery >>>>>>>>>>>>>>>>>>>>>>>>"

# # start Celery worker
celery -A setup worker --loglevel=info --broker=$CELERY_BROKER_URL_API --result-backend=$CELERY_RESULT_BACKEND_API &

# # start celery beat
celery -A setup beat --loglevel=info --broker=$CELERY_BROKER_URL_API --result-backend=$CELERY_RESULT_BACKEND_API &

sleep 5
echo "<<<<<<<<<<<<<<<<<<<< START API >>>>>>>>>>>>>>>>>>>>>>>>"
python manage.py runserver 0.0.0.0:8000
# Start the API with gunicorn
# gunicorn --bind 0.0.0.0:8000 setup.wsgi --reload --access-logfile '-' --workers=2
