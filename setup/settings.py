"""
Django settings for setup project.

Generated by 'django-admin startproject' using Django 3.1.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.1/ref/settings/
"""
import os
from datetime import timedelta
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "@yxw+2^(foid*3-@@uvjpm)!to+63zo4-%^3&_@((-+5%po=p-"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    # "*",
    "api.boostedchat.com",
    "127.0.0.1",
    "34.74.147.25",
    "34.74.147.250",
    "a69c-105-60-202-188.ngrok-free.app",
    "3e6a-62-8-92-218.ngrok-free.app",
    "203e-62-8-92-218.ngrok-free.app",
    "api.booksy.us.boostedchat.com",
    "booksy.us.boostedchat.com",
    "ce2d-105-161-11-162.ngrok-free.app",
    "https://ed48-196-105-37-1.ngrok-free.app",
    "web",
    "api",
]
CSRF_TRUSTED_ORIGINS = ["https://api.boostedchat.com",
"https://api.booksy.us.boostedchat.com",
"https://a69c-105-60-202-188.ngrok-free.app",
"https://3e6a-62-8-92-218.ngrok-free.app",
"https://3e6a-62-8-92-218.ngrok-fr",
"https://ce2d-105-161-11-162.ngrok-free.app",
"https://ed48-196-105-37-1.ngrok-free.app"

]
DIALOGFLOW_BASE_URL = (
    "https://us-central1-dialogflow.googleapis.com/v3beta1/projects/boostedchatapi/locations/us-central1/"
)
OPENAI_BASE_URL = "https://api.openai.com/v1"
# Application definition

MQTT_BASE_URL = "http://mqtt:3000"
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_beat",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "rolepermissions",
    "auditlog",
    "softdelete",
    "authentication.apps.AuthenticationConfig",
    "roles.apps.RolesConfig",
    "instagram.apps.InstagramConfig",
    "base.apps.BaseConfig",
    "settings.apps.SettingsConfig",
    "dialogflow.apps.DialogflowConfig",
    "openai.apps.OpenaiConfig",
    "sales_rep.apps.SalesRepConfig",
    "audittrails.apps.AudittrailsConfig",
    "data.apps.DataConfig",
    "leads.apps.LeadsConfig",
    "allauth",
    "allauth.account",
    "dj_rest_auth",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
    "allauth.socialaccount.providers.twitter",
]

MIDDLEWARE = [
    "dialogflow.middleware.RequestCounterMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
]

ROOT_URLCONF = "setup.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "setup.wsgi.application"

ROLEPERMISSIONS_MODULE = "roles.roles"

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases
# if DEBUG:
#     DATABASES = {
#         "default": {
#             "ENGINE": "django.db.backends.sqlite3",
#             "NAME": BASE_DIR / "boostedchatdb",  # This is where you put the name of the db file.
#             # If one doesn't exist, it will be created at migration time.
#         }
#     }
# else:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DBNAME").strip(),
        "USER": os.getenv("POSTGRES_USERNAME").strip(),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD").strip(),
        "HOST": os.getenv("POSTGRES_HOST").strip(),
        "PORT": 5432,
    }
}


AUTH_USER_MODEL = "authentication.User"

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

STATIC_URL = 'static/'
STATIC_ROOT = '/usr/src/app/static'

USE_TZ = True

# REST_USE_JWT = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

# Provider specific settings
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        # For each OAuth based provider, either add a ``SocialApp``
        # (``socialaccount`` app) containing the required client
        # credentials, or list them here:
        "APP": {"client_id": "123", "secret": "456", "key": ""}
    }
}

REST_FRAMEWORK = {"DEFAULT_AUTHENTICATION_CLASSES": ("dj_rest_auth.jwt_auth.JWTCookieAuthentication",), "PAGE_SIZE": 10}

REST_AUTH = {
    "USE_JWT": True,
}


CORS_ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://127.0.0.1:9000",
    "http://localhost:9000",
    "http://localhost:5173",
    "http://34.121.32.131",
    "https://34.121.32.131",
    "http://104.197.153.127",
    "https://104.197.153.127",
    "http://app.boostedchat.com",
    "http://booksy.us.boostedchat.com",
    "https://booksy.us.boostedchat.com",
]

CORS_ALLOW_HEADERS = (
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
)


CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CRISPY_TEMPLATE_PACK = "bootstrap4"
MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY").strip()
MAILCHIMP_DATA_CENTER = os.getenv("MAILCHIMP_DATA_CENTER").strip()
MAILCHIMP_EMAIL_LIST_ID = os.getenv("MAILCHIMP_EMAIL_LIST_ID").strip()
DEFAULT_FROM_EMAIL = os.getenv("EMAIL_HOST_USER").strip()

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER").strip()
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD").strip()
EMAIL_PORT = 587
EMAIL_USE_TLS = True

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": "",
    "AUDIENCE": None,
    "ISSUER": None,
    "JSON_ENCODER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(hours=2),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
    "TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainPairSerializer",
    "TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSerializer",
    "TOKEN_VERIFY_SERIALIZER": "rest_framework_simplejwt.serializers.TokenVerifySerializer",
    "TOKEN_BLACKLIST_SERIALIZER": "rest_framework_simplejwt.serializers.TokenBlacklistSerializer",
    "SLIDING_TOKEN_OBTAIN_SERIALIZER": "rest_framework_simplejwt.serializers.TokenObtainSlidingSerializer",
    "SLIDING_TOKEN_REFRESH_SERIALIZER": "rest_framework_simplejwt.serializers.TokenRefreshSlidingSerializer",
}
