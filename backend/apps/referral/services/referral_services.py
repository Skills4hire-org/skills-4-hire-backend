from ..models import ReferralCode, Referral

from django.db import transaction

class ReferralService:
    def __init__(self):
        pass
    
    @transaction.atomic
    def create_referral_code(self, user, code):
        try:
            code_instance, created = ReferralCode.objects.get_or_create(
                owner=user, 
                defaults={ "code": code.strip()}
            )
        except Exception as exc:
            return {"status": False, "message": str(exc)}
        return {"status": True, "instance": code_instance}
    
    def get_referral_code_instance(self, code: str) -> dict:
        if not code:
            return {"status": False, "message": "code must be prsent" }

        try:
            code_instance = ReferralCode.objects.select_related("owner").get(code=code.strip())
        except ReferralCode.DoesNotExist:
            return {"status": False, "message": "code not found"}
        
        return {"status": True, "instance": code_instance}
    
    @transaction.atomic
    def create_referral(self, referred, referrer, code_used):

        if referred is None or referrer is None:
            return {"status": False, "message": "referred or referrer must be present"}
        try:
            referral = Referral.objects.get_or_create(
                referrer=referrer,
                defaults={
                    "referred":referred,
                    "code_used": code_used
                }
            )
        except Exception as exc:
            return {"status": False, "message": str(exc)}

        return {'status': True, "instance": referral}


    def attach_referral(self, referred_user, code_str):

        if not code_str:
            return {"status": False, "message": "code must be present"}
        
        referral_code_instance = self.get_referral_code_instance(code_str)

        if not referral_code_instance['status']:
            return {"status": False, "message": referral_code_instance["message"]}
        
        code_instance = referral_code_instance['instance']

        referral = self.create_referral(

            referrer=code_instance.owner,
            referred=referred_user,
            code_used=code_instance
        )
        if not referral['status']:
            return {"status": False, "message": referral.message}

        return {"status": True, "instance": referral}



