from config.settings.base import *
import dj_database_url

DEBUG = env("DEBUG", default=False)

ALLOWED_HOSTS = ['*']

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION":env("PRODUCTION_REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
    }
}

CELERY_BROKER_URL = env("PRODUCTION_REDIS_URL", default="redis://redis:6379/0")
CELERY_RESULT_BACKEND = env("PRODUCTION_REDIS_URL", default="redis://redis:6379/1")

DATABASES = {
        'default': dj_database_url.config(
            default=env("DATABASE_URL"),
            ssl_require=True,
            conn_max_age=0
        )
    }


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("PRODUCTION_REDIS_URL")],
        },
    }
}
