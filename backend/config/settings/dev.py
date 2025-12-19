from config.settings.base import * 

# include debug toolbar in list of added apps
INSTALLED_APPS += [
    "debug_toolbar"
]

CORS_ALLOW_ALL_ORIGINS = True 


# internal ip address to enable django debug toolbar
INTERNAL_IPS = [
    "127.0.0.1"
]

# include debug toolbar middle ware
MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Overide the email backend and use the console backend for easy debugging in development

#EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend"

