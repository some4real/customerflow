from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# Load settings from Django with CELERY_ namespace
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from installed apps
app.autodiscover_tasks()

app.conf.task_acks_late = True               # Only acknowledge tasks after successful execution
app.conf.worker_prefetch_multiplier = 1      # Fetch 1 task at a time (prevents losing multiple tasks on crash)
app.conf.task_reject_on_worker_lost = True   # Re-queue tasks if worker crashes