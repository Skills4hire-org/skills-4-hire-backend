from django.conf import settings


async def validate_pusher_credentials(payload: dict) -> bool:
    payload_copy = payload.copy()
    api_key = payload_copy.get("api_key")
    secret = payload_copy.get("secret")
    app_id = payload_copy.get("app_id")
    cluster = payload_copy.get("cluster")
    
    if cluster is None:
        cluster = "en"
    required_credentials = [api_key, secret, app_id, cluster]
    if all(required_credentials):
        return True
    return False
