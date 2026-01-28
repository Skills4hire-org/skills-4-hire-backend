
from datetime import datetime

def genrate_context_for_otp(code=None, verification_url=None, email=None) -> dict:
    subject = "Your One Time Password (OTP) Code"
    return {
        "code": code,
        "email": email,
        "template_name": "authentication/otp.html",
        "subject": subject,
        "year": datetime.now().year
    }

def generate_context_for_password_reset(code, email, name) -> dict:
    subject = "Password Reset Request"
    return {
        "name": name,
        "code": code,
        "email": email,
        "template_name": "authentication/password_reset.html",
        "subject": subject,
        "year": datetime.now().year
    }