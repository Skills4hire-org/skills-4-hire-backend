import pytest
import random

from faker import Faker
from django.utils import timezone


@pytest.fixture
def setup_bookings_create():
    faker_instance = Faker()
    booking_data = {
        "address": {
            "line1": faker_instance.text(),
            "line2": faker_instance.text(),
            "city": faker_instance.city(),
            "state": faker_instance.state(),
            "country": faker_instance.country(),
            "postal_code": faker_instance.postalcode()
        },
        "price": float(random.randint(1000, 2000)),
        "notes": faker_instance.text(max_nb_chars=20),
        "descriptions": faker_instance.text(max_nb_chars=20),
        "payment_remark": faker_instance.text(max_nb_chars=20),
        "start_date": timezone.now(),
        "end_date": timezone.now() + timezone.timedelta(days=3)
    }
    return booking_data

@pytest.fixture(autouse=True)
def mock_email(monkeypatch):
    monkeypatch.setattr("apps.authentication.services.tasks.send_email_on_quene.delay", lambda x: None)