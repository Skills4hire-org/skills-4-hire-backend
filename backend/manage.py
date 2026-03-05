#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
from django.conf import settings
from dotenv import load_dotenv

import django
import os
import sys

load_dotenv()
def main():
    """Run administrative tasks."""
    setting_module = os.getenv("DJANGO_ENVIRON")

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', setting_module)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

