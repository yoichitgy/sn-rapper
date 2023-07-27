import json
import logging
import os
import random
from typing import Any

import openai
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Logging
logging.basicConfig(
    format="[%(asctime)s][%(levelname)s] %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


# Environments
UBERDUCK_API_KEY = os.environ.get("UBERDUCK_API_KEY")
UBERDUCK_SECRET_KEY = os.environ.get("UBERDUCK_SECRET_KEY")
if not UBERDUCK_API_KEY or not UBERDUCK_SECRET_KEY:
    raise ValueError(
        "Please set UBERDUCK_API_KEY and UBERDUCK_SECRET_KEY environment variables"
    )
UBERDUCK_AUTH = (UBERDUCK_API_KEY, UBERDUCK_SECRET_KEY)

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_USER_OAUTH_TOKEN")
SLACK_APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
    raise ValueError(
        "Please set SLACK_BOT_USER_OAUTH_TOKEN and SLACK_APP_TOKEN environment variables"
    )
app = App(token=SLACK_BOT_TOKEN)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY environment variable")
openai.api_key = OPENAI_API_KEY


@app.event("reaction_added")
def handle_reaction(event, say):
    logger.info(event)
    emoji = event["reaction"]
    if emoji != "rap":
        return

    item = event["item"]
    ts = item["ts"]
    channel = item["channel"]
    response = app.client.conversations_replies(channel=channel, ts=ts)
    if not response["ok"]:
        logger.error(f"Error: {response}")
        return
    message = response["messages"][0]["text"]
    logger.info(f"message: {message}")

    say(text="composing a rap song, yo! ...", thread_ts=ts)

    # lyrics = make_lyrics(message)
    # logger.info(f"lyrics: {lyrics}")

    url, lyrics = freestyle(message)
    logger.info(f"url: {url}")
    logger.info(f"lyrics: {lyrics}")

    filename = "rap.wav"
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)

    app.client.files_upload(
        file=filename,
        channels=channel,
        thread_ts=ts,
    )

    say(text=f"lyrics, yo: {lyrics}", thread_ts=ts)


def make_lyrics(text: str) -> list[list[str]]:
    """
    OBSOLETE: Use lyrics generation of uberduck.ai
    """

    model = "gpt-4"  # "gpt-3.5-turbo" or "gpt-4"
    system_prompt = (
        "Output is an array of arrays of strings in JSON format. "
        "Lines of verse, chorus, and outro are packed in an internal array. "
    )
    prompt = f"Convert the message to a rap song. \n\n```{text}```"

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )
    json_text = response["choices"][0]["message"]["content"]
    list_of_lines = json.loads(json_text)
    if not is_list_of_lists_of_str(list_of_lines):
        raise ValueError(f"Unexpected format: {list_of_lines}")

    return list_of_lines


def is_list_of_lists_of_str(data: Any) -> bool:
    if not isinstance(data, list):
        return False

    for sublist in data:
        if not isinstance(sublist, list):
            return False
        if not all(isinstance(item, str) for item in sublist):
            return False

    return True


def freestyle(subject: str) -> tuple[str, str]:
    voices = ["jsxi", "relikk", "b-la-b", "tag", "b-la-b-controllable"]
    backing_tracks = [
        ("2c3adf4e-c2b9-4419-94ee-f2f61446d07f", 105),  # Nike - Futile
        ("5fff1ec6-8736-4992-a842-8b78d37b8a8a", 90),  # Downtown - Barré
        ("1e4c6e5a-2782-4a7c-aa98-2a6c48904de5", 90),  # Prancer - Cushy
        ("6dcfd55c-c549-408d-8817-6f21efed407b", 90),  # Winners Circle - BOGER
        ("84a34767-12c0-4dc0-aa64-c292ac7d13c9", 144),  # HIGH - SANA
        ("24a7422c-9db7-495a-84bd-e1b70a42bc5a", 100),  # Mr.Krabs - YukiBeats
    ]

    voice = random.choice(voices)
    logger.info(f"voice: {voice}")

    backing_track = random.choice(backing_tracks)
    logger.info(f"backing_track: {backing_track}")

    track = backing_track[0]
    bpm = backing_track[1]
    payload = {
        "subject": subject,
        "bpm": bpm,
        "voice": voice,
        "backing_track": track,
    }
    headers = {"accept": "application/json", "content-type": "application/json"}
    url = "https://api.uberduck.ai/tts/freestyle"
    response = requests.post(
        url,
        json=payload,
        auth=UBERDUCK_AUTH,
        headers=headers,
    )
    freestyle = response.json()
    logger.debug(freestyle)

    url = str(freestyle["mix_url"])
    text_lines = [line["text"] for line in freestyle["lines"]]
    lyrics = "\n\n".join(text_lines)
    return url, lyrics


if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
