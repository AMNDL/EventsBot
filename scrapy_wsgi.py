"""
WSGI config for EventsProject project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os
from scrapy import crawler
from Events.EventsParser.spiders import main
from scrapy.utils.project import get_project_settings
from scrapy.settings import Settings
from Events.EventsParser import settings as settings_module
from django.core.wsgi import get_wsgi_application

#Подгружаем настройки Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EventsProject.settings')
application = get_wsgi_application()
crawler_settings = Settings()

#Подгружаем настройки Scrapy и запускаем парсер
crawler_settings.setmodule(settings_module)
process = crawler.CrawlerProcess(settings=crawler_settings)
spider = main.EventsSpider
process.crawl(spider)
process.start()
