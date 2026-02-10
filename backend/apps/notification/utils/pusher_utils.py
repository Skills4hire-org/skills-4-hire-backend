from pusher import Pusher
from django.conf import settings
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from asgiref.sync import sync_to_async

from .helpers import validate_pusher_credentials

PUSHER_APP_ID = getattr(settings, "PUSHER_APP_ID", None)
PUSHER_KEY = getattr(settings, "PUSHER_KEY", None)
PUSHER_SECRET = getattr(settings, "PUSHER_SECRET", None)
PUSHER_CLUSTER = getattr(settings, "PUSHER_CLUSTER", None)

@sync_to_async
def get_pusher_client() -> Pusher:
    pusher_client_payload = {
        "app_id": PUSHER_APP_ID,
        "secret": PUSHER_SECRET,
        "cluster": PUSHER_CLUSTER,
        "api_key": PUSHER_KEY
    }
    if not validate_pusher_credentials(pusher_client_payload):
        raise ValidationError(_("Invalid payload for pusher initialization, check pucher configurations"), 
                              code="invalid_reqeust")
    
    pusher_client = Pusher(
        app_id=PUSHER_APP_ID,
        secret=PUSHER_SECRET,
        key=PUSHER_KEY,
        cluster=PUSHER_CLUSTER,
        ssl=True
    )

    return pusher_client
