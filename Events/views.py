import json
import traceback
from EventsProject.settings import slack_client, env
from django.http import JsonResponse
from django.views import View
from .services import (MessageHandler,
                       Handler,
                       CallbackHandler)


class MainBotView(View):
    """ Bot View that which gets a response and sends it to the right Handler"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_handler = MessageHandler()
        self.callback_handler = CallbackHandler()

    @staticmethod
    def process_response(response: dict, handler: Handler):
        handler.handle(response)

    # Каждое сообщение боту - POST запрос,который и нужно обрабатывать
    def post(self, request, *args, **kwargs):
        try:
            response = json.loads(request.body)
            self.message_handler.set_next(self.callback_handler)
            self.process_response(response, self.message_handler)
            return JsonResponse({200: "OK"})
        except Exception as exc:
            slack_client.chat_postMessage(channel=env('SLACK_BOT_LOG_CHANNEL'), text=traceback.format_exc())
            return JsonResponse({500: "INTERNAL ERROR"})
