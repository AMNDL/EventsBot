import telebot


class MessageHandler(object):
    """ Class which processes basic chat messages """

    def __init__(self, bot: telebot.TeleBot, message: dict):
        self.__bot = bot
        self.__message_text = message['message']['text']
        self.__chat_id = message['message']['chat']['id']
        self.__message_id = message['message']['message_id']
        self._event_types = ['Планетарий', 'Спектакли', 'Концерты', 'Фестивали',
                             'Спорт', 'Детям', 'Шоу', 'Юмор', 'Кино']
        self._keyboard = Keyboard(None, self._event_types)

    def process_message(self):
        """ Perform an action according to the message text"""

        if self.__message_text == '/start':
            # Send reply_keyboard when the bot starts working

            reply_markup = self._keyboard.reply_keyboard.to_json()
            text = 'Доступные команды:'

            self.__bot.delete_message(self.__chat_id, self.__message_id)
            self.__bot.send_message(
                self.__chat_id, text=text, reply_markup=reply_markup)

        elif self.__message_text == '/help':
            # Send help message

            self.__bot.send_message(self.__chat_id,
                                    """Привет,я бот,который поможет вам выбрать интересное мероприятие.Выберите интересующий Вас тип события и удобную дату,после чего Вы сможете ознакомиться с событием подробнее и приобрести билеты на него\n\n\n/start   -начало работы,вывод доступных команд бота\n/help   -справочник команд\n/random   -выбрать случайное события""")

        elif self.__message_text == 'Выбрать тип события':
            # Send inline keyboard with event_types

            reply_markup = self._keyboard.events_keyboard.to_json()
            text = 'Выберите тип события:'

            self.__bot.send_message(
                self.__chat_id, text=text, reply_markup=reply_markup)

        elif self.__message_text in {'Случайное событие', '/random'}:
            # Send random message

            event = EventsModel.rand_manager.random()
            send_event_data(event, self.__chat_id, self.__bot)

        else:

            self.__bot.send_message(self.__chat_id, 'Не понимаю')
            self.__bot.send_sticker(self.__chat_id,
                                    data='CAACAgIAAxkBAAIIhl8Fni6uWPIIVIipZ-_3H1sTb7d4AAICAQACVp29Ck7ibIHLQOT_GgQ')

class CallbackHandler(object):
    """ Class which processes basic chat messages """

    def __init__(self, bot: telebot.TeleBot, callback: dict):
        self.__bot = bot
        self.__callback_data = callback['callback_query']['data']
        self.__chat_id = callback['callback_query']['message']['chat']['id']
        self.__message_id = callback['callback_query']['message']['message_id']
        self._event_types = ['Планетарий', 'Спектакли', 'Концерты', 'Фестивали',
                             'Спорт', 'Детям', 'Шоу', 'Юмор', 'Кино']
        self._keyboard = Keyboard(self.__callback_data, self._event_types)
        self.__reply_markup = callback['callback_query']['message']['reply_markup'][
            'inline_keyboard']

    def process_callback(self):
        """ Perform an action according to the callback message"""
        if self.__callback_data == 'categories':
            # Delete previous message and send inline keyboard with categories

            reply_markup = self._keyboard.events_keyboard.to_json()
            text = 'События'
            self.__bot.delete_message(self.__chat_id, self.__message_id)
            self.__bot.send_message(self.__chat_id, text,
                                    reply_markup=reply_markup)

        elif self.__callback_data in self._event_types:
            # Delete previous message and send dates inlinte keyboard

            reply_markup = self._keyboard.upcoming_dates_keyboard.to_json()
            text = 'Ближайшие даты'
            self.__bot.delete_message(self.__chat_id, self.__message_id)
            self.__bot.send_message(self.__chat_id, text,
                                    reply_markup=reply_markup)

        elif len(self.__callback_data.split(' ')) == 2:
            # Process data that looks like  ( 00-00-0000 Data)

            event_date = self.__callback_data.split(' ')

            if 'available_dates' in event_date:
                # Send the list of inline buttons with available dates for the chosen event type

                dates = DatabaseManager(
                    EventsModel).get_dates_list(event_date[0])
                self.__bot.delete_message(self.__chat_id, self.__message_id)
                self.__bot.send_message(self.__chat_id, 'Доступные даты:',
                                        reply_markup=self._keyboard.available_dates_keyboard(dates,event_date[0]))

            elif 'show_more' in event_date:
                # Load more inline date buttons
                dates = DatabaseManager(
                    EventsModel).get_dates_list(event_date[0])
                new_keyboard = self._keyboard.add_dates_to_markup(
                    self.__reply_markup, dates, event_date[0])
                self.__bot.edit_message_reply_markup(
                    self.__chat_id, message_id=self.__message_id, reply_markup=new_keyboard)

            else:
                # Send all appropriate events

                formatted_callback = f'{event_date[0]} {event_date[1]}'
                events = DatabaseManager(EventsModel).get_events_list(formatted_callback)

                if len(events) != 0:
                    self.__bot.delete_message(self.__chat_id, self.__message_id)
                    for event in events:
                        send_event_data(event, self.__chat_id, self.__bot)

                else:
                    self.__bot.send_message(
                        self.__chat_id, 'Событий на эту дату не запланировано')


class Keyboard(object):
    """ Class which allows to get different keyboard markups"""

    @staticmethod
    def events_keyboard(event_types):
        """ Создать разметку клавиатуры для типов событий """
        events_markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        for item in range(0, len(event_types), 3):
            btn1 = telebot.types.InlineKeyboardButton(
                f'{event_types[item]}', callback_data=f'{event_types[item]}')
            btn2 = telebot.types.InlineKeyboardButton(
                f'{event_types[item + 1]}', callback_data=f'{event_types[item + 1]}')
            btn3 = telebot.types.InlineKeyboardButton(
                f'{event_types[item + 2]}', callback_data=f'{event_types[item + 2]}')
            events_markup.add(btn1, btn2, btn3)
        events_markup.add(telebot.types.InlineKeyboardButton(
            'Другое', callback_data='Другое'))
        return events_markup

    @property
    def upcoming_dates_keyboard(self):
        """ Get markup for keyboard with 8 dates from today inclusively"""
        today = datetime.datetime.today()
        tomorrow = today + datetime.timedelta(days=1)
        day_after_tomorrow = today + datetime.timedelta(days=2)
        dates_markup = telebot.types.InlineKeyboardMarkup(row_width=3)
        btn_today = telebot.types.InlineKeyboardButton(
            'Сегодня', callback_data=f'{self.__callback_data} {today.strftime("%Y-%m-%d")}')
        btn_tomorrow = telebot.types.InlineKeyboardButton(
            'Завтра', callback_data=f'{self.__callback_data} {tomorrow.strftime("%Y-%m-%d")}')
        btn_after_tomorrow = telebot.types.InlineKeyboardButton(
            day_after_tomorrow.strftime("%d.%m.%Y"),
            callback_data=f'{self.__callback_data} {day_after_tomorrow.strftime("%Y-%m-%d")}')
        dates_markup.add(btn_today, btn_tomorrow, btn_after_tomorrow)
        for item in range(3, 9, 3):
            new_date_1 = today + datetime.timedelta(days=item)
            new_date_2 = today + datetime.timedelta(days=item + 1)
            new_date_3 = today + datetime.timedelta(days=item + 2)

            one = telebot.types.InlineKeyboardButton(new_date_1.strftime("%d.%m.%Y"),
                                                     callback_data=f'{self.__callback_data} {new_date_1.strftime("%Y-%m-%d")}')
            two = telebot.types.InlineKeyboardButton(new_date_2.strftime("%d.%m.%Y"),
                                                     callback_data=f'{self.__callback_data} {new_date_2.strftime("%Y-%m-%d")}')
            three = telebot.types.InlineKeyboardButton(new_date_3.strftime("%d.%m.%Y"),
                                                       callback_data=f'{self.__callback_data} {new_date_3.strftime("%Y-%m-%d")}')
            dates_markup.add(one, two, three)

        dates_markup.add(
            telebot.types.InlineKeyboardButton('Выбрать тип события', callback_data='categories'),
            telebot.types.InlineKeyboardButton('Доступные даты',
                                               callback_data=f'{self.__callback_data} available_dates'))

        return dates_markup

    @property
    def reply_keyboard(self):
        """ Get markup for reply keyboard with 2 buttons"""

        reply_markup = telebot.types.ReplyKeyboardMarkup(row_width=1)

        reply_markup.add(telebot.types.KeyboardButton('Выбрать тип события'))
        reply_markup.add(telebot.types.KeyboardButton('Случайное событие'))

        return reply_markup

    def available_dates_keyboard(self, dates: list, event_type: str):
        """ Get markup for the list with available dates """

        markup = telebot.types.InlineKeyboardMarkup()

        if len(dates) >= 5:
            dates = dates[:5]
            show_more = True

        else:
            show_more = False

        for date in dates:
            cb_date = datetime.datetime.strptime(date, "%d.%m.%Y").strftime("%Y-%m-%d")
            markup.add(telebot.types.InlineKeyboardButton(
                f'{date}', callback_data=f'{event_type} {cb_date}')
            )

        if show_more:
            markup.add(telebot.types.InlineKeyboardButton(
                f'Показать еще', callback_data=f'{event_type} show_more'))
        return markup

    def add_dates_to_markup(self, markup_lists: list, dates_list, event_type: str):
        """ Get markup of dates list with additional dates"""

        reply_markup = telebot.types.InlineKeyboardMarkup()
        markup_lists = markup_lists[:-1]
        used_dates = [item[0]['text'] for item in markup_lists]
        not_used_dates = dates_list[dates_list.index(used_dates[-1]) + 1:]
        show_more = False

        if len(not_used_dates) > 5:
            not_used_dates = not_used_dates[:5]
            show_more = True

        for date in used_dates + not_used_dates:
            formatted_date = datetime.datetime.strptime(
                date, "%d.%m.%Y").strftime("%Y-%m-%d")
            reply_markup.add(telebot.types.InlineKeyboardButton(
                f'{date}', callback_data=f'{event_type} {formatted_date}'))

        if show_more:
            reply_markup.add(telebot.types.InlineKeyboardButton(
                f'Показать еще', callback_data=f'{event_type} show_more'))

        return reply_markup


class DatabaseManager(object):

    def __init__(self, model):
        # Django model object
        self.__model = model

    def get_events_list(self, message_text: str):
        """ Get a list of all events from the text like 'Event Date' """
        return self.__model.objects.annotate(
            search=SearchVector('event_type') + SearchVector('date'),
        ).filter(search=message_text)

    def get_random_event(self):
        """ Get random model object"""
        return self.__model.rand_manager.random()

    def get_dates_list(self, event_type: str):
        """ Get all available dates for a certain event type"""
        formatted_dates = list()
        raw_dates = sorted(self.__model.objects.filter(
            event_type=event_type).values_list('date__date', flat=True).distinct())
        for date in raw_dates:
            formatted_dates.append(date.strftime("%d.%m.%Y"))

        return formatted_dates


def send_event_data(event, chat_id, bot):
    """ Function which sends necessary event data to the user """
    caption = f"""<b>{event.title}\n</b><b>Тип события: </b><i>{event.event_type}\n</i><b>Дата: {event.date}\n</b><b>Цена Билета: </b><i>{event.price}\n</i><b>Место: </b><i>{event.location}\n</i>
                """

    markup = telebot.types.InlineKeyboardMarkup()

    event_button = telebot.types.InlineKeyboardButton(
        text='Подробнее', url=event.event_link
    )
    ticket_button = telebot.types.InlineKeyboardButton(
        text="Билеты", url=event.ticket_link
    )

    if event.ticket_link != 'Билеты отсутствуют':
        markup.add(event_button, ticket_button)
    else:
        markup.add(event_button)

    reply_markup = markup.to_json()

    bot.send_photo(
        chat_id,
        photo=event.image,
        caption=caption,
        parse_mode='HTML',
        reply_markup=reply_markup
    )
