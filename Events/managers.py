import re
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import datetime
from Events.models import Event
from typing import Union, List


class KeyboardMarkupManager(object):
    """ Class, creating markups for different keyboard types """

    @staticmethod
    def _get_events_list_chunks(events_list: list, size: int = 3):
        """ create list of equal size lists to use them in inline buttons """
        events_chunks = []
        for i in range(0, len(events_list), size):
            events_chunks.append(events_list[i:i + size])
        return events_chunks

    def events_keyboard(self, event_types: list):
        """ Create markup for events keyboard """
        events_markup = InlineKeyboardMarkup(row_width=3)
        event_chunks = self._get_events_list_chunks(event_types)
        for events_chunk in event_chunks:
            # add several event buttons in one line to events markup
            events_markup.add(*[InlineKeyboardButton(f'{event_type}', callback_data=f'{event_type}')
                                for event_type in events_chunk])
        return events_markup

    @staticmethod
    def _get_closest_dates(event_type: str, start_date: datetime.date, use_words: bool = True) -> tuple:
        tomorrow = start_date + datetime.timedelta(days=1)
        after_tomorrow = start_date + datetime.timedelta(days=2)
        btn_start_date = InlineKeyboardButton('Сегодня' if use_words else start_date.strftime('%d.%m.%Y')
                                              , callback_data=f'{event_type} {start_date.strftime("%Y-%m-%d")}')
        btn_tomorrow = InlineKeyboardButton('Завтра' if use_words else tomorrow.strftime('%d.%m.%Y'),
                                            callback_data=f'{event_type} {tomorrow.strftime("%Y-%m-%d")}')
        btn_after_tomorrow = InlineKeyboardButton(after_tomorrow.strftime("%d.%m.%Y"),
                                                  callback_data=f'{event_type} {after_tomorrow.strftime("%Y-%m-%d")}')
        return btn_start_date, btn_tomorrow, btn_after_tomorrow

    def _get_date_buttons_list(self, event_type: str, start_date: datetime.date) -> List[tuple]:
        use_words = True if start_date == datetime.datetime.today().date() else False
        date_buttons_list = [self._get_closest_dates(event_type, start_date, use_words)]
        for days_diff in range(3, 9, 3):
            date_btn1 = InlineKeyboardButton(None)
            date_btn2 = InlineKeyboardButton(None)
            date_btn3 = InlineKeyboardButton(None)
            for idx, btn in enumerate([date_btn1, date_btn2, date_btn3]):
                date = start_date + datetime.timedelta(days=days_diff + idx)
                btn.callback_data = f'{event_type} {date.strftime("%Y-%m-%d")}'
                btn.text = f'{date.strftime("%d.%m.%Y")}'
            date_buttons_list.append((date_btn1, date_btn2, date_btn3))
        last_date = date.strftime("%Y-%m-%d")
        first_date = (datetime.datetime.strptime(last_date, "%Y-%m-%d")
                      - datetime.timedelta(days=8)).strftime("%Y-%m-%d")
        pagination_buttons = [(InlineKeyboardButton('<', callback_data=f'{event_type} {first_date} dates_back'),
                               InlineKeyboardButton('>', callback_data=f'{event_type} {last_date} dates_forward'))]
        additional_commands_buttons = [(InlineKeyboardButton('Выбрать тип события', callback_data='categories'),
                                        InlineKeyboardButton('Доступные даты',
                                                             callback_data=f'{event_type} available_dates'))]
        return pagination_buttons + date_buttons_list + additional_commands_buttons

    def upcoming_dates_keyboard(self, event_type: str, start_date: datetime.date):
        """ Создать разметку клавиатуры для 8 следующих дат включительно"""
        dates_markup = InlineKeyboardMarkup(row_width=3)
        markup_buttons = self._get_date_buttons_list(event_type, start_date)
        for buttons in markup_buttons:
            dates_markup.add(*buttons)
        return dates_markup

    @staticmethod
    def available_dates_keyboard(dates: list, event_type: str):
        """ Get markup for the list with available dates """

        markup = InlineKeyboardMarkup()

        if len(dates) >= 5:
            dates = dates[:5]
            show_more = True
        else:
            show_more = False

        for date in dates:
            cb_date = datetime.datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d")
            markup.add(InlineKeyboardButton(
                f'{date}', callback_data=f'{event_type} {cb_date}'))

        if show_more:
            markup.add(InlineKeyboardButton(
                f'Показать еще', callback_data=f'{event_type} show_more_dates'))
        markup.add(InlineKeyboardButton(
            f'Выбрать тип события', callback_data=f'categories'))
        return markup

    @staticmethod
    def add_dates_to_markup(markup_lists: list, dates_list: list, event_type: str):
        """ Add dates to dates list markup """

        reply_markup = InlineKeyboardMarkup()
        markup_lists = markup_lists[:-1]
        used_dates = [item[0]['text'] for item in markup_lists
                      if re.match(r'\d{2}.\d{2}.\d{4}', item[0]['text'])]
        not_used_dates = dates_list[dates_list.index(used_dates[-1]) + 1:]
        show_more = False

        if len(not_used_dates) > 5:
            not_used_dates = not_used_dates[:5]
            show_more = True

        # add previously not printed dates to existing markup
        for date in used_dates + not_used_dates:
            # reformat the string because d.m.y is more comfortable for users and y.m.d can be used in django lookup
            formatted_date = datetime.datetime.strptime(
                date, "%d.%m.%Y").strftime("%Y-%m-%d")
            reply_markup.add(InlineKeyboardButton(
                f'{date}', callback_data=f'{event_type} {formatted_date}'))

        if show_more:
            reply_markup.add(InlineKeyboardButton(
                f'Показать еще', callback_data=f'{event_type} show_more_dates'))
        reply_markup.add(InlineKeyboardButton(
            f'Выбрать тип события', callback_data=f'categories'))

        return reply_markup


class DatabaseManager(object):

    def __init__(self, model=Event):
        self.model = model

    def get_events_list(self, event_date: Union[str, datetime.date], event_type: str = None):
        """ Get a list of all events with defined type and date """
        return (list(self.model.objects.filter(event_type=event_type, date__date=event_date))
                if event_type
                else list(self.model.objects.filter(date__date=event_date)))

    def get_random_event(self):
        """ Get random model object"""
        return self.model.rand_manager.random()

    def get_dates_list(self, event_type: str):
        """ Get all available dates for a certain event type"""
        formatted_dates = list()
        raw_dates = sorted(self.model.objects.filter(
            event_type=event_type, date__gte=datetime.datetime.now()).values_list('date__date', flat=True).distinct())
        for date in raw_dates:
            formatted_dates.append(date.strftime("%d.%m.%Y"))
        return formatted_dates


class OutputManager(object):

    def __init__(self, bot: telebot.TeleBot):
        self.bot = bot

    @staticmethod
    def format_event_data(event: Event, chat_id: int):
        event_price = event.price if event.price else 'Не указана'
        # event representation breaks if indents are added to the caption
        caption = f"""<b>{event.title}\n\n</b><b>Тип события: </b><i>{event.event_type}\n</i><b>Дата: </b><i>{event.date}\n</i><b>Цена Билета: </b><i>{event_price}\n</i><b>Место: </b><i>{event.location}\n</i>"""
        markup = InlineKeyboardMarkup()
        event_button = InlineKeyboardButton(text='Подробнее', url=event.event_link)
        ticket_button = InlineKeyboardButton(text="Билеты", url=event.ticket_link)
        if event.ticket_link:
            markup.add(event_button, ticket_button)
        else:
            markup.add(event_button)

        return dict(
            chat_id=chat_id,
            photo=event.image,
            caption=caption,
            parse_mode='HTML',
            reply_markup=markup, )

    def send_event_data(self, event: Event, chat_id: int,
                        event_date: Union[str, datetime.date] = '',
                        event_type: str = None,
                        last_printed_event_id: int = None, is_last: bool = False):
        """ Function which sends necessary event data to the user """
        format_event = self.format_event_data(event, chat_id)
        # if last_printed_event_id is None, it means that the event is the last which should be printed
        # otherwise event_id can equal >= 0
        if is_last:
            format_event['reply_markup'].add(InlineKeyboardButton(text='Выбрать другую дату',
                                                                  callback_data=event_type))
            format_event['reply_markup'].add(InlineKeyboardButton(text='Выбрать тип события',
                                                                  callback_data='categories'))
        elif last_printed_event_id is not None:
            format_event['reply_markup'].add(
                InlineKeyboardButton(text='Еще события',
                                     callback_data=f'{event_type} {event_date} {last_printed_event_id}'))
            format_event['reply_markup'].add(InlineKeyboardButton(text='Выбрать тип события',
                                                                  callback_data='categories'))
        format_event['reply_markup'] = format_event['reply_markup'].to_json()
        self.bot.send_photo(**format_event)

    def send_all_events_data(self, events: list, chat_id: int, last_event_id: int,
                             event_date: Union[str, datetime.date] = '',
                             event_type: str = None):
        events_chunk = events[last_event_id:last_event_id + 5]
        is_last = False
        if events_chunk[-1] == events[-1]:
            is_last = True
            last_event_id = None
        else:
            last_event_id = last_event_id + 5
        for event in events_chunk[:-1]:
            self.send_event_data(event, chat_id)
        self.send_event_data(events_chunk[-1], chat_id, event_date=event_date, event_type=event_type,
                             last_printed_event_id=last_event_id, is_last=is_last)
