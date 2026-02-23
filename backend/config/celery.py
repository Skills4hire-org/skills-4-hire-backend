import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

setting_module = os.getenv("DJANGO_ENVIRON")
debug = os.getenv('DEBUG')

if setting_module.endswith("prod") and debug is False:
    os.environ.setdefault("DJANGO_SETTINGS_MODULT", setting_module)
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", setting_module)

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()
