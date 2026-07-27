from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import AdminRegistrationSerializer, AdminLoginSerializer
from ...core.exceptions import api_response

class AdminRegistrationViewset(viewsets.ModelViewSet):
    http_method_names = ['post']
    serializer_class = AdminRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return api_response(
            message="Registration Successful", 
            status_code=201, data={'success': True, "user": {'id': str(user.pk)}})

class AdminLoginView(TokenObtainPairView):
    serializer_class = AdminLoginSerializer
    