# Try to import Celery app, but don't fail if it's not installed
try:
    from .celery import app as celery_app
    __all__ = ("celery_app",)
except ImportError:
    # Celery not installed - development mode without task queue
    celery_app = None
    __all__ = ("celery_app",)
