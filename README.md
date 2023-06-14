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

## Docker Setup
OS X Instructions
- Build images - docker-compose build
- Start services - docker-compose up -d
- Create migrations - docker-compose run web /usr/local/bin/python manage.py migrate

## Endpoints
4. Endpoints available in this api are as follows:
- api/v1/ [name='users']
- api/v1/authentication/token/obtain/ [name='token_create']
- api/v1/authentication/token/refresh/ [name='token_refresh']
- api/v1/authentication/register [name='register']
- api/v1/authentication/login [name='login']
- api/v1/authentication/logout/ [name='rest_logout']
- api/v1/authentication/user/ [name='rest_user_details']
- api/v1/authentication/auth/google/ [name='google_login']
- api/v1/authentication/auth/facebook/connect/ [name='fb_connect']
- api/v1/authentication/auth/twitter/connect/ [name='twitter_connect']
- api/v1/authentication/socialaccounts/ [name='social_account_list']
- api/v1/authentication/socialaccounts/<int:pk>/disconnect/ [name='social_account_disconnect']
- api/v1/authentication/verify-email/ [name='rest_verify_email']
- api/v1/authentication/resend-email/ [name='rest_resend_email']
- api/v1/authentication/^account-confirm-email/(?P<key>[-:\w]+)/$ [name='account_confirm_email']
- api/v1/authentication/account-email-verification-sent/ [name='account_email_verification_sent']
- api/v1/authentication/password/change/ [name='rest_password_change']
- api/v1/authentication/password/reset/ [name='rest_password_reset']
- api/v1/authentication/password/reset/confirm/<str:uidb64>/<str:token> [name='password_reset_confirm']
- api/v1/instagram/ ^account/$ [name='account-list']
- api/v1/instagram/ ^account\.(?P<format>[a-z0-9]+)/?$ [name='account-list']
- api/v1/instagram/ ^account/(?P<pk>[^/.]+)/$ [name='account-detail']
- api/v1/instagram/ ^account/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$ [name='account-detail']
- api/v1/instagram/ ^comment/$ [name='comment-list']
- api/v1/instagram/ ^comment\.(?P<format>[a-z0-9]+)/?$ [name='comment-list']
- api/v1/instagram/ ^comment/(?P<pk>[^/.]+)/$ [name='comment-detail']
- api/v1/instagram/ ^comment/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$ [name='comment-detail']
- api/v1/instagram/ ^hashtag/$ [name='hashtag-list']
- api/v1/instagram/ ^hashtag\.(?P<format>[a-z0-9]+)/?$ [name='hashtag-list']
- api/v1/instagram/ ^hashtag/(?P<pk>[^/.]+)/$ [name='hashtag-detail']
- api/v1/instagram/ ^hashtag/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$ [name='hashtag-detail']
- api/v1/instagram/ ^photo/$ [name='photo-list']
- api/v1/instagram/ ^photo\.(?P<format>[a-z0-9]+)/?$ [name='photo-list']
- api/v1/instagram/ ^photo/(?P<pk>[^/.]+)/$ [name='photo-detail']
- api/v1/instagram/ ^photo/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$ [name='photo-detail']
- api/v1/instagram/ ^video/$ [name='video-list']
- api/v1/instagram/ ^video\.(?P<format>[a-z0-9]+)/?$ [name='video-list']
- api/v1/instagram/ ^video/(?P<pk>[^/.]+)/$ [name='video-detail']
- api/v1/instagram/ ^video/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$ [name='video-detail']
- api/v1/instagram/ ^reel/$ [name='reel-list']
- api/v1/instagram/ ^reel\.(?P<format>[a-z0-9]+)/?$ [name='reel-list']
- api/v1/instagram/ ^reel/(?P<pk>[^/.]+)/$ [name='reel-detail']
- api/v1/instagram/ ^reel/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$ [name='reel-detail']
- api/v1/instagram/ ^story/$ [name='story-list']
- api/v1/instagram/ ^story\.(?P<format>[a-z0-9]+)/?$ [name='story-list']
- api/v1/instagram/ ^story/(?P<pk>[^/.]+)/$ [name='story-detail']
- api/v1/instagram/ ^story/(?P<pk>[^/.]+)\.(?P<format>[a-z0-9]+)/?$ [name='story-detail']
