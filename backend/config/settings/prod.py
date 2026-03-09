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

if not DEBUG:
    SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE', default=True, cast=bool)
    CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', default=True, cast=bool)
    SECURE_HSTS_SECONDS = env('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True