import os

from celery import Celery

celery_app = Celery(
    "app",
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6377/0"),
    broker=os.getenv("CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//"),
)

celery_app.autodiscover_tasks(["app"])
