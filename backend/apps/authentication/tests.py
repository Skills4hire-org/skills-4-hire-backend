from django.test import TestCase
from apps.authentication.services.tasks import send_email_notification
from rest_framework.response import Response
from datetime import datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions

@api_view(http_method_names=["GET"])
@permission_classes(permission_classes=[permissions.AllowAny])
def test_email_service(request):

    name="ogenna israel"
    context= {
            "name": name,
            "app_name": "app_name",
            "year": datetime.now().year
        }
    subject="hello"
    receipient = "ogennaisrael@gmail.com"
    try:

        send_email_notification.delay(
            subject,
            context,
            "authentication/test.html",
            receipient
        )
    except Exception as e:
        raise e

    return Response({"message": "email sent"})

