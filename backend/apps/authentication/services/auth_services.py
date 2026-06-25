from django.conf import settings

from google.oauth2 import id_token
from google.auth.transport import requests

request_instance = requests.Request()
client_id = getattr(settings, 'GOOGLE_CLIENT_ID')

def verify_google_token(token: str) -> dict[str, any]:
    try:
        response = id_token.verify_oauth2_token(
            id_token=token, request=request_instance, audience=str(client_id)
        )
        return {
            "status": True, "user_id": response.get("sup"),
            "email": response.get("email"), "name": response.get('name'),
            "email_verified": response.get("email_verified")
        }

    except Exception as exc:
        return {
            "status": False,
            "message": str(exc)
        }

def google_auth(token: str) -> dict[str, any]:
    return verify_google_token(token=token)



def facebook_auth(token: str) -> dict[str, any]:
    pass

def apple_auth(token: str) -> dict[str, any]:
    pass