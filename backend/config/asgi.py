
import os

from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

from channels.routing import ProtocolTypeRouter, URLRouter
from apps.notification.routings import websocket_urlpatterns

load_dotenv()

setting_module = os.getenv("DJANGO_SETTINGS_MODULE")

os.environ.setdefault('DJANGO_SETTINGS_MODULE',  setting_module)

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(websocket_urlpatterns),
})
