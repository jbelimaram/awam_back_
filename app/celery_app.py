import ssl
from celery import Celery
from celery.schedules import crontab

from app.core.config import REDIS_URL

celery_app = Celery(
    "awam",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.agenda_tasks"],
)

celery_app.conf.broker_use_ssl = {
    "ssl_cert_reqs": ssl.CERT_NONE,
}

celery_app.conf.redis_backend_use_ssl = {
    "ssl_cert_reqs": ssl.CERT_NONE,
}

celery_app.conf.timezone = "Africa/Tunis"
celery_app.conf.enable_utc = False

celery_app.conf.beat_schedule = {
    "check-agenda-reminders": {
        "task": "app.tasks.agenda_tasks.check_and_send_reminders",
        "schedule": crontab(minute="*/15"),
    },
}