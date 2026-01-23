from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions

@api_view(http_method_names=["GET"])
@permission_classes(permission_classes=[permissions.AllowAny])
def health(request):
    print(request.auth)
    return JsonResponse(data={
       "status": "success",
       "paths": {
           "auth": "api/v1/auth/",
           "users": "api/v1/users",
           "posts": "api/v1/posts",
           "bookings": "api/v1/bookings"
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
