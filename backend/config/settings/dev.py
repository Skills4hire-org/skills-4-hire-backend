from config.settings.base import *
import dj_database_url

import ssl

from pygments.lexer import default

ALLOWED_HOSTS = ["*"]

DEBUG = env.bool("DEBUG")

if DEBUG:
    INSTALLED_APPS += ["debug_toolbar", "silk"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]


    MIDDLEWARE += ["silk.middleware.SilkyMiddleware"]

    SILKY_PYTHON_PROFILER = True
    SILKY_META = True
    SILKY_ANALYZE_QUERIES = True

    INTERNAL_IPS = [ "127.0.0.1", "localhost" ]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("DEV_REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
    }
}

CELERY_BROKER_URL = env("DEV_REDIS_URL", default="redis://localhost:6379")
CELERY_RESULT_BACKEND = env("DEV_REDIS_URL", default="redis://localhost:6379")


CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    "https://hoppscotch.io",
]

# DATABASES = {
#     "default": dj_database_url.config(
#         default=env("DATABASE_URL"),
#         ssl_require=True,
#         conn_max_age=0
#     )
# }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "database.sqlite3",
    }
}


CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                {
                    "address": env("DEV_REDIS_URL"),
                    "ssl_cert_reqs": None,
                }
            ],
        },
    },
}

