from config.settings.base import *

DEBUG = env("DEBUG")

ALLOWED_HOSTS = ['127.0.0.1']

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION":env("REDIS_INTERNAL_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
    }
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/1")

DATABASES = {
        'default': {
            'ENGINE': env("POSTGRES_ENGINE"),
            'NAME': env("POSTGRES_NAME"),
            "USER": env("POSTGRES_USER"),
            "PASSWORD": env("POSTGRES_PASSWORD"),
            "PORT": env("POSTGRES_PORT"),
            "HOST": env("POSTGRES_HOST"),
            "POOL_MODE": env("POSTGRES_POLL_MODE"),
            "OPTIONS": {
                "sslmode": "require",
            },
            "CONN_MAX_AGE": 0,
        }
    }
