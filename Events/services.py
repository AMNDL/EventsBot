import telebot
import datetime
import dateparser
from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from EventsProject.settings import env
from Events.models import Event
from Events.managers import (KeyboardMarkupManager,
                             DatabaseManager,
                             OutputManager)
from re import match


class Handler(ABC):
    """
    The Handler interface declares a method for building a chain of handlers.
    It also declares a method to make the request.
    """

    @abstractmethod
    def set_next(self, handler):
        pass

    @abstractmethod
    def handle(self, request) -> Optional[str]:
        pass


class AbstractHandler(Handler):

    def __init__(self):
        self.bot = telebot.TeleBot(env('BOT_TOKEN'))
        self.event_types = Event.EventType.labels
        self._next_handler = None
        self.keyboard_manager = KeyboardMarkupManager()
        self.db_manager = DatabaseManager()
        self.output_manager = OutputManager(self.bot)

    def set_next(self, handler: Handler) -> Handler:
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, response: Any) -> str:
        if self._next_handler:
            return self._next_handler.handle(response)

    def send_events(self, events: list, chat_id, last_printed_event_idx, event_date='', event_type=None):
        if events:
            self.output_manager.send_all_events_data(events, chat_id, last_printed_event_idx,
                                                     event_date=event_date, event_type=event_type, )
            print('Выведены события')
        else:
            self.bot.send_message(chat_id, 'Событий на эту дату не запланировано')


class MessageHandler(AbstractHandler):
    """ Usual text message handler """

    def handle(self, response: dict) -> str:

        # if response is not a message, send response to another handler
        if not response.get('message'):
            return super().handle(response)
        message_text = response['message'].get('text')
        chat_id = response['message']['chat']['id']
        message_id = response['message']['message_id']
        if message_text == '/start':
            self.bot.send_message(chat_id, 'Выберите тип события',
                                  reply_markup=self.keyboard_manager.events_keyboard(self.event_types))
            return 'Message Processed'
        elif message_text == '/random':
            event = self.db_manager.get_random_event()
            if not event:
                self.bot.send_message(chat_id, 'База данных пустая')
                return 'Message processed'
            self.output_manager.send_event_data(event, chat_id)
            return 'Message processed'
        elif message_text == '/help':
            self.bot.send_message(chat_id,
                                  """Привет,я бот,который поможет вам выбрать интересное мероприятие.Выберите интересующий Вас тип события и удобную дату,после чего Вы сможете ознакомиться с событием подробнее и приобрести билеты на него\n\n\n/start   -начало работы,вывод доступных команд бота\n/help   -справочник команд\n/random   -выбрать случайное события""")
        self.bot.send_message(chat_id, 'Я Вас не понимаю')
        self.bot.send_sticker(chat_id, 'CAACAgIAAxkBAAIR-2Bu6ibhjcD-_tz-rkkuv8m6LPMQAAKCAgACVp29Ctoil7Tbmco2HgQ')


class CallbackHandler(AbstractHandler):
    """ Callback messages handler """

    def send_categories(self, chat_id: int):
        """ Send message including categories keyboard """
        markup = self.keyboard_manager.events_keyboard(self.event_types)
        self.bot.send_message(chat_id, 'Выберите тип события', reply_markup=markup)
        print('Выведены категории событий')

    def send_available_dates(self, chat_id: int, event_type: str):
        """ Send list of available dates of defined event type """
        dates_list = self.db_manager.get_dates_list(event_type)
        if dates_list:
            markup = self.keyboard_manager.available_dates_keyboard(dates_list, event_type)
            self.bot.send_message(chat_id, 'Список доступных дат:', reply_markup=markup)
            print('Выведены доступные даты события')
        else:
            self.bot.send_message(chat_id, 'В ближайшее время нет событий')

    def show_more_dates(self, event_type: str, markup_items: list, chat_id: int, message_id: int):
        """ Add dates to event dates keyboard """
        dates_list = self.db_manager.get_dates_list(event_type)
        markup = self.keyboard_manager.add_dates_to_markup(markup_items, dates_list, event_type)
        self.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=markup)
        print('К списку событий добавлены события')

    def paginate_dates(self, chat_id, message_id, keyboard_command, event_date, event_type):
        """ Replace event type dates keyboard with future or previous dates keyboard """
        if keyboard_command == 'dates_forward':
            first_data = (datetime.datetime.strptime(event_date, '%Y-%m-%d') + datetime.timedelta(days=1)).date()
            dates_markup = self.keyboard_manager.upcoming_dates_keyboard(event_type, first_data)
            self.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=dates_markup)
            print('Клавиатура с датами обновлена вперед')
        elif keyboard_command == 'dates_back':
            first_data = (datetime.datetime.strptime(event_date, '%Y-%m-%d') - datetime.timedelta(days=9)).date()
            if first_data >= datetime.datetime.today().date():
                dates_markup = self.keyboard_manager.upcoming_dates_keyboard(event_type, first_data)
                self.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=dates_markup)
                print('Клавиатура с датами обновлена назад')
        else:
            self.bot.send_message(chat_id, 'Неизвестная команда')

    def process_callback_data(self, event_type: str, event_date: Union[str, datetime.date],
                              keyboard_command: str, last_printed_event_idx: int, markup_items: list,
                              chat_id: int, message_id: int):
        """ Send message to a user according to the parsed callback values """
        if event_type and not any({keyboard_command, event_date}):
            markup = self.keyboard_manager.upcoming_dates_keyboard(event_type, datetime.datetime.today().date())
            self.bot.send_message(chat_id, 'Выберите дату события', reply_markup=markup)
            print('Выведена клавиатура с датами')
        elif all({event_type, event_date, keyboard_command}):
            self.paginate_dates(chat_id, message_id, keyboard_command, event_date, event_type)
        elif event_type and keyboard_command:
            if keyboard_command == 'available_dates':
                self.send_available_dates(chat_id, event_type)
                print('Выведен список доступных дат')
            elif keyboard_command == 'show_more_dates':
                self.show_more_dates(event_type, markup_items, chat_id, message_id)
                print('Добавлены даты к списку дат')
            else:
                self.bot.send_message(chat_id, 'Неизвестная команда')
        elif event_type and event_date:
            events = self.db_manager.get_events_list(event_date, event_type=event_type)
            if events:
                self.output_manager.send_all_events_data(events, chat_id, last_printed_event_idx,
                                                         event_date=event_date, event_type=event_type, )
                print('Выведены события')
            else:
                self.bot.send_message(chat_id, 'Событий на эту дату не запланировано')
        elif keyboard_command == 'categories':
            self.send_categories(chat_id)
        else:
            self.bot.send_message(chat_id, 'Событий на эту дату не запланировано')

    def handle(self, response: dict) -> Union[str, None]:
        # if response is not a callback, send response to another handler
        if not response.get('callback_query'):
            return super().handle(response)

        callback_text = response['callback_query']['data']
        chat_id = response['callback_query']['message']['chat']['id']
        message_id = response['callback_query']['message']['message_id']
        markup_items = response['callback_query']['message']['reply_markup']['inline_keyboard']
        callback_data_list = callback_text.split()
        print(callback_text)
        event_type = (callback_data_list[0]
                      if callback_data_list and callback_data_list[0] in self.event_types
                      else None)
        event_date = (callback_data_list[1]
                      if len(callback_data_list) > 1 and match(r'\d{4}-\d{2}-\d{2}', callback_data_list[1])
                      else None)
        keyboard_command = ''
        # used for dates pagination
        last_printed_event_idx = 0
        # callback_text = {keyboard_command}
        if not event_type:
            keyboard_command = callback_text
        # callback_text = {event_type} {keyboard_command}
        elif not event_date and len(callback_data_list) > 1:
            keyboard_command = callback_data_list[1]
        elif event_type and event_date and len(callback_data_list) > 2:
            # callback_text = {event_type} {event_date} {last_printed_event_idx}
            if callback_data_list[-1].isdigit():
                last_printed_event_idx = int(callback_data_list[-1])
            # callback_text = {event_type} {event_date} {keyboard_command}
            else:
                keyboard_command = callback_data_list[-1]
        self.process_callback_data(event_type, event_date, keyboard_command,
                                   last_printed_event_idx, markup_items, chat_id, message_id)
