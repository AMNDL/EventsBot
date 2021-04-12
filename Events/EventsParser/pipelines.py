# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import psycopg2
import dateparser
import datetime
import traceback
import pathlib
from ..models import Event
from scrapy.pipelines.files import FilesPipeline
from EventsProject.settings import slack_client, env
from scrapy.exceptions import CloseSpider


class EventsParserPipeline(object):

    def process_item(self, item, spider):
        """ Format event description and date text """
        try:
            if item['date'] is not None:
                item['date'] = dateparser.parse(item['date'].replace(',', '')).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as exc:
            slack_client.chat_postMessage(channel=env('SLACK_PARSER_LOG_CHANNEL'), text=traceback.format_exc())
            raise CloseSpider(str(exc))
        return item


class EventsTypePipeline(object):

    def process_item(self, item, spider):
        """ Change event type text"""
        try:
            event_type = item['event_type']
            if 'Детские' in event_type:
                item['event_type'] = Event.EventType.CHILD

            elif 'Юмор' in event_type:
                item['event_type'] = Event.EventType.HUMOR

            elif 'Другие' in event_type:
                item['event_type'] = Event.EventType.OTHERS

            elif 'Спорт' in event_type:
                item['event_type'] = Event.EventType.SPORTS
        except Exception as exc:
            slack_client.chat_postMessage(channel=env('SLACK_PARSER_LOG_CHANNEL'), text=traceback.format_exc())
            raise CloseSpider(str(exc))
        return item


class EventsParserImagePipeline(FilesPipeline):
    """ Download image into media folder and add link to the Item object"""

    def item_completed(self, results, item, info):
        try:
            for is_captured, image in results:
                if is_captured:
                    image_path = pathlib.Path(image["path"])
                    item['image'] = str(image_path)
        except Exception as exc:
            slack_client.chat_postMessage(channel=env('SLACK_PARSER_LOG_CHANNEL'), text=traceback.format_exc())
            raise CloseSpider(str(exc))
        del item['file_urls']
        return item


class EventsParserPostgresPipeline(object):
    """ Export item data to the database """

    def process_item(self, item, spider):
        try:
            if not Event.objects.filter(date=item['date'], title=item['title'], event_type=item['event_type']):
                Event.objects.update_or_create(**item)

        except Exception as exc:
            slack_client.chat_postMessage(channel=env('SLACK_PARSER_LOG_CHANNEL'), text=traceback.format_exc())
            raise CloseSpider(str(exc))
        return item
