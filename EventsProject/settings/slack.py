from .settings import env
from slack_sdk import WebClient

slack_client = WebClient(token=env('SLACK_BOT_TOKEN'))
