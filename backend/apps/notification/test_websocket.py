from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from rest_framework import serializers, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request

from .services import trigger_notification

class TestSerializer(serializers.Serializer):
    message = serializers.CharField(write_only=True)



@csrf_exempt
@api_view(http_method_names=["POST"])
@permission_classes([permissions.IsAuthenticated])
def test_websocket(request: Request):
    user = request.user
    user_pk  = str(user.pk)
    serializer = TestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data
    message = data["message"] if data else "Hello"
    try:
        trigger_notification(user_pk=user_pk, event=message)
    except Exception:
        raise Exception("Failed to send notification")

    return Response({"status": "success", "message": "Notification sent"},status=status.HTTP_200_OK)


def index(request):
    return render(request, 'notification/index.html', status=200)
