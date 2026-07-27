from django.contrib.auth.password_validation import validate_password as _validate_password
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from ...authentication.helpers import validate_email

UserModel = get_user_model()

class AdminRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = [
            "email", "password"
        ]

    def validate_email(self, value):
        valid_email = validate_email(value)
        if UserModel.objects.filter(email=valid_email).exists():
            raise serializers.ValidationError("Invalid Email. User with this email already exists")

        return valid_email

    def validate_password(self, value):
        _validate_password(value)
        return value

    def create(self, validated_data):
        validated_data.update({"active_role": "ADMIN"})
        return UserModel.objects.create_superuser(**validated_data)
    


class AdminLoginSerializer(TokenObtainPairSerializer):
    def _admin_can_authenticate(self, user: UserModel):
        if hasattr(user, "is_active") and user.is_active:
            return user.is_staff and user.is_superuser and user.is_verified
        return False

    def validate(self, attrs):
        email = attrs["email"]
        user = get_object_or_404(UserModel, email=email)

        if not self._admin_can_authenticate(user=user):
            raise serializers.ValidationError("User not active to login")

        if not user.check_password(attrs['password']):
            raise serializers.ValidationError("Invalid password")

        update_last_login(None, user=user)
        return super().validate(attrs)