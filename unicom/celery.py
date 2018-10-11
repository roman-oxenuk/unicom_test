# -*- coding: utf-8 -*-
import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unicom.settings')

app = Celery('unicom')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.timezone = 'UTC'

app.conf.beat_schedule = {
    'match-customers-with-offers-every-10-minutes': {
        'task': 'applications.tasks.match_customers_with_offers_task',
        'schedule': 60,    # Раз в 1 минуту (60 секунд)
    },
}
