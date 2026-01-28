from django.test import TestCase
from django.contrib.auth import get_user_model

from .helpers import _send_email_to_user
from .utils.helpers import create_otp_for_user
from .utils.template_helpers import genrate_context_for_otp

User = get_user_model()

def tst_email_service(request):
    ...    


class EmailNotifTest(TestCase):
    def setUp(self):
        user = User.objects.create_user(email="test_user@example.com", password="0987poiu")

    # def test_send_email_to_user(self):
    #     user = User.objects.first()
    #     result = _send_email_to_user()
    #     print(result)

    def test_generate_context(self):
        user = User.objects.first()
        code = "0988"
        email = user.email
        result = genrate_context_for_otp(code=code, email=email)
        print(result)


