import celery
import os
from scrapy import crawler
from .EventsParser.spiders import main
from scrapy.settings import Settings
from .EventsParser import settings as settings_module
from django.core.wsgi import get_wsgi_application


class EventsParser(celery.Task):

    def run(self, *args, **kwargs):
        pass

    @staticmethod
    def parse_events():
        # Подгружаем настройки Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EventsProject.settings')
        application = get_wsgi_application()
        crawler_settings = Settings()

        # Подгружаем настройки Scrapy и запускаем парсер
        crawler_settings.setmodule(settings_module)
        process = crawler.CrawlerProcess(settings=crawler_settings)
        spider = main.EventsSpider
        process.crawl(spider)
        process.start()


@celery.shared_task(bind=True, base=EventsParser)
def parse_all_events(self):
    self.parse_events()
