from django.core.exceptions import ValidationError    

def _validate_subject_or_context(subject, context):
    """ 
    A simple function that validate sent subject and context
    """
    try:
        if not subject or str(subject).strip():
            subject  = "Unkown subject"
        else:
            subject = str(subject).strip().title()

        if not isinstance(context, dict):
            raise ValidationError("Context can only be passed in dict format")

        return True
    except (ValueError, ValidationError) :
        raise


