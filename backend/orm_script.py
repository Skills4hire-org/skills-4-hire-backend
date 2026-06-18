import channels.layers
from asgiref.sync import async_to_sync
from dotenv import load_dotenv

import django
import os
load_dotenv()

setting_module = os.getenv("DJANGO_SETTINGS_MODULE")

os.environ.setdefault('DJANGO_SETTINGS_MODULE',  setting_module)
django.setup()

def run():
    print("Run")

if __name__ == "__main__":
    print(run())
