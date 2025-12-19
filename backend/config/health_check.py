from django.http import JsonResponse
from rest_framework.decorators import api_view

@api_view(http_method_names=["GET"])
def health(request):
    return JsonResponse(data={
        "SUCCESS": True,
        "message": "Django is alive and active"
    }
    )


@api_view(http_method_names=["GET"])
def check_docker_update(request):
    return JsonResponse(data={
        "success": True,
        "message": "docker is up and running"
    })
