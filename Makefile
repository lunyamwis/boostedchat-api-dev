clean:
	@ echo 'cleaning...'
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*.log' -delete



makemigrations:
	@ echo 'creating migrations...'
	python manage.py makemigrations

migrate:
	@ echo 'creating migrations...'
	python manage.py migrate

install:
	@ echo 'Installing dependencies...'
	python -m pip install -r requirements.txt

upgrade:
	@ echo 'Upgrading dependencies'
	pre-commit run django-upgrade --all-files

roles:
	@ echo 'Synchronizing roles'
	python manage.py sync_roles

test:
	coverage run --source=. manage.py test --verbosity=2  && coverage report -m

run:
	@ echo 'starting server...'
	python manage.py runserver


lint:
	@ echo 'linting...'
	flake8 .

run_celery:
	celery -A app worker -l info --pool=gevent
