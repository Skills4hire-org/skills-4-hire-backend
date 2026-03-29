
def generate_context_for_endorsement_email(
        email, endorsement_url, 
        full_name, frontend_url, 
        sender_full_name, APP_name, template_name
):

    subject = f"Endorsement Update On {APP_name}"

    return {
        "subject": subject,
        "email": email,
        "full_name": full_name,
        'sender_full_name': sender_full_name,
        "app_name": APP_name,
        "frontend_url": frontend_url,
        'endorsement_url': endorsement_url,
        "template_name": template_name
    }