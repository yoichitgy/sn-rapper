"""
This module is just used to try out the Slack API and test the bot.
"""

import logging
import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Logging
logging.basicConfig(
    format="[%(asctime)s][%(levelname)s] %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)

# Environments
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_USER_OAUTH_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError(
        "Please set SLACK_BOT_USER_OAUTH_TOKEN and SLACK_APP_TOKEN environment variables"
    )

app = App(token=SLACK_BOT_TOKEN)


@app.message("knock knock")
def ask_who(message, say):
    say("_Who's there?_")


@app.event("app_mention")
def respond_to_mention(event, say):
    message = event["text"]
    say(message)


@app.event("reaction_added")
def handle_reaction(event, say):
    print(event)
    emoji = event["reaction"]
    if emoji == "rap":
        item = event["item"]
        ts = item["ts"]
        channel = item["channel"]
        response = app.client.conversations_replies(channel=channel, ts=ts)
        if response["ok"]:
            message = response["messages"][0]["text"]
            say(text=message, thread_ts=ts)
        else:
            print(f"Error: {response}")

        app.client.files_upload(
            file="mix.wav",
            channels=channel,
            thread_ts=ts,
        )


SocketModeHandler(app, SLACK_APP_TOKEN).start()
