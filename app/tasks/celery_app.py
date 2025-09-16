from celery import Celery
from app.config import settings


celery_app = Celery(
    "file_api",
    broker=settings.CELERY_BROKER_URL,
    include=[
        "app.tasks.thumbnails",
        ]
)
celery_app.autodiscover_tasks(["app.tasks"])


# на всякий
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Almaty",
    enable_utc=True,
)