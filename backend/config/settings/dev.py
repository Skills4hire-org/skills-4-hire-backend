from config.settings.base import * 

DEBUG = env("DEBUG")

ALLOWED_HOSTS = ["*"]

DEBUG = env.bool("DEBUG")
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    INSTALLED_APPS += ["silk"]

    MIDDLEWARE += ["silk.middleware.SilkyMiddleware"]

    SILKY_PYTHON_PROFILER = True
    SILKY_META = True
    SILKY_ANALYZE_QUERIES = True

INTERNAL_IPS = [ "127.0.0.1", "localhost" ]

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
    }
}

CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/0"

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = [
    "https://hoppscotch.io",
]