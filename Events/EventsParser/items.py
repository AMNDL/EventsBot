# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class EventsParserItem(scrapy.Item):
    event_type = scrapy.Field()
    title = scrapy.Field()
    date = scrapy.Field()
    price = scrapy.Field()
    location = scrapy.Field()
    file_urls = scrapy.Field()
    ticket_link = scrapy.Field()
    event_link = scrapy.Field()
    image = scrapy.Field()
