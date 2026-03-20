
import os

from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

from apps.notification.routings import websocket_urlpatterns

load_dotenv()

setting_module = os.getenv("DJANGO_SETTINGS_MODULE")

os.environ.setdefault('DJANGO_SETTINGS_MODULE',  setting_module)

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
    )
})
