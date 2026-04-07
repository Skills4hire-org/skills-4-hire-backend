import uuid
import random
import string

def reference() -> str:
    return f"Skills4Hire-{uuid.uuid4()}-{"".join(random.choice(string.ascii_letters) for _ in range(5))}"
    