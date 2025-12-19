
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

django.setup()

from apps.authentication.otp_models import OTP_Base
from django.utils import timezone

def ready():
    code = OTP_Base.objects.first()

    print(code.created_at)
    print(timezone.now())

if __name__ == "__main__":
    ready()