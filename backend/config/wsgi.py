
import os

from django.core.wsgi import get_wsgi_application
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

setting_module = os.getenv("DJANGO_SETTINGS_MODULE", "config.settings.prod")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', setting_module)

application = get_wsgi_application()
