## Features

- Django, Django REST Framework, and Python
- Custom user model
- Token-based auth
- Signup/login/logout
- [django-allauth](https://github.com/pennersr/django-allauth) for social auth

## First-time setup

1.  Make sure Python 3.7x and Pipenv are already installed. [See here for help](https://djangoforbeginners.com/initial-setup/).
2.  Clone the repo and configure the virtual environment:

```
$ git clone  https://github.com/LUNYAMWIDEVS/boostedchat-api.git
$ cd boostedchat-api
$ pip install -r requirements.txt
```

3.  Set up the initial migration for our custom user models in users and build the database.

```
(drfx) $ python manage.py makemigrations 
(drfx) $ python manage.py migrate
(drfx) $ python manage.py createsuperuser
(drfx) $ python manage.py runserver
```

