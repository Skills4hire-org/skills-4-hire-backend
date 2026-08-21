from typing import Any
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken

from django.contrib.auth import get_user_model

UserModel = get_user_model()


@database_sync_to_async
def get_user(token):
    try:

        access_token = AccessToken(token=token)
        user_id  = access_token.get("user_id")

        user = UserModel.objects.get(pk=user_id, is_active=True)
        return user
    except Exception:
        return AnonymousUser()


class AuthMiddleware:
    def __init__(self, inner) -> None:
        self.inner = inner

    async def __call__(self, scope, receive, send) -> Any:
        print(scope)
        query_string = scope.get("query_string", b"").decode("utf-8")

        query_params = parse_qs(query_string)
        token = query_params.get("token")
        if token:
            token = token[0]
            scope['user'] = await get_user(token=token)
        else:
            scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, send)
