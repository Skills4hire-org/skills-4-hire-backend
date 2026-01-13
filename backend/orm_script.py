
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

django.setup()

import redis


def ready():
    r = redis.Redis(host="127.0.0.1", port=6379, db=0)
    print(r.ping())
    
if __name__ == "__main__":
    ready()


