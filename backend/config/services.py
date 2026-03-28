from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.exceptions import ValidationError

@api_view(http_method_names=["GET"])
@permission_classes(permission_classes=[permissions.AllowAny])
def health(request):
    print(request.auth)
    return JsonResponse(data={
       "status": "success",
       "paths": {
           "auth": "api/v1/auth/",
           "users": "api/v1/users/",
           "posts": "api/v1/posts/",
           "bookings": "api/v1/bookings/"
       }
    }
    )



@api_view(http_method_names=["GET"])
@permission_classes(permission_classes=[permissions.AllowAny])
def check_docker_update(request):
    return JsonResponse(data={
        "success": True,
        "message": "docker is up and running"
    })


@api_view(http_method_names=["GET"])
@permission_classes(permission_classes=[permissions.AllowAny])
def test_email(request):
   
    from django.core.mail import send_mail
    from django.conf import settings

    subject = 'Hello Bro'
    message = 'New Message'

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email="skills4hireofficial@gmail.com",
            recipient_list=['ogennaisrael@gmail.com'],
            fail_silently=False,
        )
    except Exception as e:
        raise ValidationError(f"Error: {e}")

    return JsonResponse(data={'message':"Sent"})
    