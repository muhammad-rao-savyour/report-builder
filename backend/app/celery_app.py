"""Celery setup.

The settings here are the difference between a toy and something that survives
a server being killed mid-job.

  task_acks_late              - the message is removed from RabbitMQ only AFTER
                                the task finishes. If the worker dies at 90%,
                                another worker picks the job up again.
  worker_prefetch_multiplier  - 1 means a worker grabs one job at a time. The
                                default (4) makes a worker hoard four big jobs
                                while other idle workers sit doing nothing.
  time limits                 - a task that hangs forever holds a worker slot
                                forever. Always set a ceiling.
"""
from celery import Celery

from .config import settings

celery_app = Celery(
    "app",
    broker=settings.broker_url,
    include=["app.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    task_time_limit=60 * 60,
    task_soft_time_limit=55 * 60,
    broker_connection_retry_on_startup=True,
    result_backend=None,
)
