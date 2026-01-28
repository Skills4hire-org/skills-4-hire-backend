
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

django.setup()

import redis


def ready():
   
if __name__ == "__main__":
    ready()


