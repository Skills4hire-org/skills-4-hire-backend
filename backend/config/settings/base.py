import os
from pathlib import Path
import environ

from django.utils import timezone
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(MAIL_ENABLED=(bool, False), SMTP_LOGIN=(str, "DEFAULT"))

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = ""

ALLOWED_HOSTS = []

RESEND_API_KEY = env("RESEND_API_KEY")
RESEND_REQUEST_PATH = env("RESEND_REQUEST_PATH")
FROM_EMAIL = env("FROM_EMAIL")

# UTILS
BASE_URL = env("BASE_URL")
OTP_RETRIES_PER_DAY = env.int("OTP_RETRIES_PER_DAY")
MAX_OTP_LENGTH = env.int("MAX_OTP_LENGTH")
APP_NAME = env("APP_NAME", default="Skills4Hire")
OTP_EXPIRY = env.int("OTP_EXPIRY")
RESTRICTED_PATHS = env("RESTRICTED_PATHS").split(",")


# User model to user 
AUTH_USER_MODEL = "authentication.CustomUser"

# SETTING MODULE
DJANGO_ENVIRON= env("DJANGO_ENVIRON")

# Channels Config
ASGI_APPLICATION = "config.asgi.application"

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third party apps
    'corsheaders',
    'cloudinary',
    'cloudinary_storage',
    "drf_yasg",
    "rest_framework",
    'django_celery_beat',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    "django_countries",
    "channels",

    # local apps
    'apps.authentication.apps.AuthenticationConfig',
    "apps.users.apps.UsersConfig",
    "apps.posts.apps.PostsConfig",
    "apps.ratings.apps.RatingsConfig",
    "apps.bookings.apps.BookingsConfig",
    "apps.wallet.apps.WalletConfig",
    "apps.notification.apps.NotificationConfig",
    'apps.chats.apps.ChatsConfig',

]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'PAGE_SIZE': env('DEFAULT_PAGE_SIZE', default=20, cast=int),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': env('THROTTLE_RATE_ANON', default='100/hour'),
        'user': env('THROTTLE_RATE_USER', default='1000/hour'),
    },
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=env('JWT_ACCESS_TOKEN_LIFETIME', default=1440, cast=int)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        minutes=env('JWT_REFRESH_TOKEN_LIFETIME', default=10080, cast=int)
    ),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JTI_CLAIM': 'jti',
    'TOKEN_TYPE_CLAIM': 'token_type',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
}

AUTHENTICATION_BACKENDS = [
    "apps.authentication.backends.CustomBackend",
    'django.contrib.auth.backends.ModelBackend'
]


CLOUDINARY = {
        "CLOUD_NAME": env("CLOUD_NAME"),
        "API_KEY": env("CLOUD_API_KEY"),
        "API_SECRET": env("CLOUD_API_SECRET_KEY"),

        'BASE_URL': f"https://res.cloudinary.com/{env('CLOUD_NAME')}/",
        "AVATER_FOLDER": env("CLOUDINARY_PROFILE_FOLDERS"),
        "SECURE": True
    }

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.authentication.middleware.RateLimitOtpRequestMiddleware',
    
]

ROOT_URLCONF = 'config.urls'

 
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery config
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
timezone = 'Africa/Lagos'

CELERY_BEAT_SCHEDULE = {
    "delete_otp": {
        "task": "apps.authentication.services.tasks.auto_delete_otp",
        "schedule": crontab(minute="*/5")
    },
    "auto_delete_exp_outstanding_jwt": {
        "task": "apps.authentication.services.tasks.clean_up_expired_jwt",
        "schedule": crontab(hour=0, minute=0)
    },
    "auto_update_roles": {
        "task": "apps.users.tasks.auto_update_role",
        "schedule": crontab(minute=1)
    }
}
CORS_ALLOWED_ORIGINS = env(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://localhost:8000',
)

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# CSRF Settings
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# Security Headers
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", "'unsafe-inline'"),
    'style-src': ("'self'", "'unsafe-inline'"),
}


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': env('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'conversations': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


os.makedirs(BASE_DIR / 'logs', exist_ok=True)
