from .settings import *


OPENAI_API_KEY = "your open ai api key here"


STRIPE_SECRET_KEY = "stripe secret key here"
STRIPE_PUBLIC_KEY = "stripe public key here"
STRIPE_WEBHOOK_SECRET = "stripe webhook secret"


UNSPLASH_ACCESS_KEY = "unsplash access key here"


EMAIL_HOST_PASSWORD = "email host password here"


DEBUG = True
IS_DEV = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
SECRET_KEY = "django-insecure-dyb_8=*dg&-81#5leycizjybho@5un+4#4k2_ui+&tr)2-r(s$"
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

DOMAIN = "http://127.0.0.1:8000"
