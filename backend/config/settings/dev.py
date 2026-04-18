from config.settings.base import *

ALLOWED_HOSTS = ["*"]

DEBUG = env.bool("DEBUG")

if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]


    # MIDDLEWARE += ["silk.middleware.SilkyMiddleware"]

    # SILKY_PYTHON_PROFILER = True
    # SILKY_META = True
    # SILKY_ANALYZE_QUERIES = True

    INTERNAL_IPS = [ "127.0.0.1", "localhost" ]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
    }
}

CELERY_RESULT_BACKEND = 'django-db'
CELERY_BROKER_POOL_LIMIT = 1  # Limits the number of connections to the broker
CELERY_REDIS_MAX_CONNECTIONS = 5 # Limits connections per worker
CELERY_BROKER_URL = env("redis://localhost:6379/0", default="redis://redis:6379/0")
# CELERY_RESULT_BACKEND = env("PRODUCTION_REDIS_URL", default="redis://redis:6379/1")


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
                    "address": "redis://localhost:6379/",
                    "ssl_cert_reqs": None,
                }
            ],
        },
    },
}

