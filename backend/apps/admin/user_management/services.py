from django.contrib.auth import get_user_model

UserModel = get_user_model()

def delete_user_account(user: UserModel):
    user.is_deleted = True
    user.is_active = False
    user.save(update_fields=['is_deleted'])
    return user

def suspend_user_account(user: UserModel):
    user.is_active = False
    user.save(update_fields=['is_active'])
    return user
