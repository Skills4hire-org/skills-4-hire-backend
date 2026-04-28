import secrets

def generate_code(user):
    prefix = user.full_name[:3].upper() if len(user.full_name) > 4 else "USER"
    suffix = secrets.token_urlsafe(4).upper()[:5]
    return f"{prefix}-{suffix}"


def generate_reference_key(user):
    suffix  = secrets.token_urlsafe(16)[:12]
    return f"{generate_code(user)}-{suffix}".lower()