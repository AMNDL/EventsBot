import scrapy
import traceback
from ..items import EventsParserItem
from EventsProject.settings import slack_client, env
from scrapy.exceptions import CloseSpider


class EventsSpider(scrapy.Spider):
    name = 'events'
    allowed_domains = ['kharkov.internet-bilet.ua', ]
    start_urls = [
        'https://kharkov.internet-bilet.ua/ru/events-rubric/4/theater',
        'https://kharkov.internet-bilet.ua/ru/events-rubric/3/concert',
        'https://kharkov.internet-bilet.ua/ru/events-rubric/18/festival',
        'https://kharkov.internet-bilet.ua/ru/events-rubric/7/sport',
        'https://kharkov.internet-bilet.ua/ru/events-rubric/9/child',
        'https://kharkov.internet-bilet.ua/ru/events-rubric/24/planetariy',
        'https://kharkov.internet-bilet.ua/ru/events-rubric/15/show',
        'https://kharkov.internet-bilet.ua/ru/events-rubric/16/kino',
        'https://kharkov.internet-bilet.ua/ru/events-rubric/19/yumor',
        'https://kharkov.internet-bilet.ua/ru/events-rubric/21/others',
    ]
    user_agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36 OPR/42.0.2393.94'

    def parse(self, response):
        """ Page pagination and following events pages """
        try:
            section_title = response.css('h1.page-title::text').get().replace('Харькова', '').strip('\n ')
            for event in response.css('a.btn.order-btn.e-badge'):
                yield response.follow(event, callback=self.parse_item,
                                      cb_kwargs={'event_type': section_title})

            button = response.css('div.pagination a')
            """ Follow pagination button  """
            if button != [] and button[-1].css('::text').get() == 'вперед>':
                yield response.follow(button[-1], callback=self.parse)
        except Exception as exc:
            slack_client.chat_postMessage(channel=env('SLACK_PARSER_LOG_CHANNEL'), text=traceback.format_exc())
            raise CloseSpider(str(exc))

    def parse_item(self, response, event_type: str):
        """ Parse data from event page """
        info = EventsParserItem()
        info['ticket_link'] = None
        try:
            if 'Отмена' not in response.css('div.event-info-warning-block div.title::text').get(default=''):
                # Check that buy_tickets button is available
                if response.css('a.btn.btn-color.middle.btn-tickets::attr(href)').get() is not None:
                    info['ticket_link'] = 'https://kharkov.internet-bilet.ua' + response.css(
                        'a.btn.btn-color.middle.btn-tickets::attr(href)').get()

                info['date'] = response.css('div.date-bar .date::text').get()
                info['title'] = response.css('.event-title::text').get()
                info['event_type'] = event_type
                info['price'] = response.css('div.col-info-without-border strong::text').get()
                info['location'] = response.css('div.place span span::text').get()
                # info['description'] = response.css(
                #     '.descr-unified ::text').getall()
                info['file_urls'] = ['https://kharkov.internet-bilet.ua' + response.css(
                    'a.fancybox-photo img::attr(src)').get()]
                info['event_link'] = response.url
                yield info
        except Exception as exc:
            slack_client.chat_postMessage(channel=env('SLACK_PARSER_LOG_CHANNEL'), text=traceback.format_exc())
            raise CloseSpider(str(exc))
