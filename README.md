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

## Endpoints
4. Endpoints available in this api are as follows:
- api/v1/ token/obtain/ [name='token_create']
- api/v1/ token/refresh/ [name='token_refresh']
- api/v1/ register [name='register']
- api/v1/ login [name='login']
- api/v1/ users [name='users']
- api/v1/ dj-rest-auth/google/ [name='google_login']
- api/v1/ dj-rest-auth/facebook/connect/ [name='fb_connect']
- api/v1/ dj-rest-auth/twitter/connect/ [name='twitter_connect']
- api/v1/ socialaccounts/ [name='social_account_list']
- api/v1/ socialaccounts/<int:pk>/disconnect/ [name='social_account_disconnect']
- api/v1/ verify-email/ [name='rest_verify_email']
- api/v1/ resend-email/ [name='rest_resend_email']
- api/v1/ verify-email/ [name='rest_verify_email']
- api/v1/ resend-email/ [name='rest_resend_email']
- api/v1/ ^account-confirm-email/(?P<key>[-:\w]+)/$[name='account_confirm_email']
- api/v1/ account-email-verification-sent[name='account_email_verification_sent']
- api/v1/ password/reset/ [name='rest_password_reset']
- api/v1/ password/reset/confirm/ [name='rest_password_reset_confirm']
- api/v1/ logout/ [name='rest_logout']
- api/v1/ user/ [name='rest_user_details']
- api/v1/ password/change/ [name='rest_password_change']
