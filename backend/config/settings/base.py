import os
from pathlib import Path
import environ
from django.utils import timezone
from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(MAIL_ENABLED=(bool, False), SMTP_LOGIN=(str, "DEFAULT"))

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
print(BASE_DIR)
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG")

ALLOWED_HOSTS = ['127.0.0.1', "localhost", "skills-4-hire-backend.onrender.com"]


BASE_URL = env("BASE_URL")
OTP_RETRIES_PER_DAY = env.int("OTP_RETRIES_PER_DAY")
MAX_OTP_LENGTH = env.int("MAX_OTP_LENGTH")
APP_NAME = env("APP_NAME")
OTP_EXPIRY = env.int("OTP_EXPIRY")
RESTRICTED_PATHS = env("RESTRICTED_PATHS").split(",")
# User model to user 
AUTH_USER_MODEL = "authentication.CustomUser"

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

    # local apps
    'apps.authentication.apps.AuthenticationConfig',
    "apps.users.apps.UsersConfig",
    "apps.posts.apps.PostsConfig",
    "apps.ratings.apps.RatingsConfig"

]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.CursorPagination',
    'PAGE_SIZE': 100
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated"
    ]

}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timezone.timedelta(days=2),
    "REFRESH-TOKEN_LIFETIME": timezone.timedelta(days=3),
    "UPDATE_LAST_LOGIN": True,
    "USER_ID_FIELD": "user_id",
    "USER_ID_CLAIM": "user_id",
    "ROTATE_REFRESH_TOKEN": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",)
}

AUTHENTICATION_BACKENDS = [
    "apps.authentication.backends.EmailPhoneBackend",
    'django.contrib.auth.backends.ModelBackend'
]


CLOUDINARY = {
        "CLOUD_NAME": env("CLOUD_NAME"),
        "API_KEY": env("CLOUD_API_KEY"),
        "API_SECRET": env("CLOUD_API_SECRET_KEY"),

        'BASE_URL': f"https://res.cloudinary.com/{env("CLOUD_NAME")}/",
        "AVATER_FOLDER": env("CLOUDINARY_PROFILE_FOLDERS"),
        "SECURE": True
    }

DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("LOCATION"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        }
    }
}

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

if DEBUG: 
    DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
else:
    DATABASES = {
        'default': {
            'ENGINE': env("POSTGRES_ENGINE"),
            'NAME': env("POSTGRES_NAME"),
            "USER": env("POSTGRES_USER"),
            "PASSWORD": env("POSTGRES_PASSWORD"),
            "PORT": env("POSTGRES_PORT"),
            "HOST": env("POSTGRES_HOST")
        }
    }



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

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# Celery config
CELERY_BROKER_URL = env("redis://redis:6379/0", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("redis://redis:6379/0", default="redis://localhost:6379/1")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
timezone = 'Africa/Lagos'

CELERY_BEAT_SCHEDULE = {
    "delete_otp": {
        "task": "apps.authentication.services.tasks.auto_delete_otp",
        "schedule": crontab(hour=10, minute=0)
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


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler"
        }
    },
    "loggers": {
        "rest_framework": {
            "handlers": ["console"],
            "level": "DEBUG"
        },
    },
}
