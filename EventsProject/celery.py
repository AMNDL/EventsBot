import os
import sys
from celery import Celery
from celery.schedules import crontab

# На винде не работает мультипроцессинг
if sys.platform == 'win32':
    os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EventsProject.settings')
celery_app = Celery('EventsProject')
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
celery_app.conf.update(CELERY_TIMEZONE='Europe/Kiev')
celery_app.autodiscover_tasks()

celery_app.conf.beat_schedule = {
    'parse_events': {
        'task': 'Events.tasks.parse_all_events',
        'schedule': crontab(hour='4', minute=0, ),
        'args': (),
    },
}
