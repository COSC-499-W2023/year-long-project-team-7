from .settings import *

OPENAI_API_KEY = "your openai api key here"

DEBUG = True

EMAIL_HOST_PASSWORD = "your email host password here"

SECRET_KEY = "django-insecure-dyb_8=*dg&-81#5leycizjybho@5un+4#4k2_ui+&tr)2-r(s$"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "dev",
        "USER": "postgres",
        "PASSWORD": "password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
