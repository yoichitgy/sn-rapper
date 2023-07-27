import json
import logging
import os
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

    lyrics = make_lyrics(message)
    logger.info(f"lyrics: {lyrics}")

    url = freestyle(lyrics)
    logger.info(f"url: {url}")

    filename = "rap.wav"
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)

    app.client.files_upload(
        file=filename,
        channels=channel,
        thread_ts=ts,
    )

    lyrics_text = "\n\n".join([" ".join(line) for line in lyrics])
    say(text=f"lyrics, yo: {lyrics_text}", thread_ts=ts)


def make_lyrics(text: str) -> list[list[str]]:
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


def freestyle(lyrics: list[list[str]]) -> str:
    voices = ["jsxi", "relikk"]
    backing_tracks = [
        ("2c3adf4e-c2b9-4419-94ee-f2f61446d07f", 105),  # Nike - Futile
        ("5fff1ec6-8736-4992-a842-8b78d37b8a8a", 90),  # Downtown - Barré
    ]

    backing_track = backing_tracks[0][0]
    bpm = backing_tracks[0][1]
    lines = sum(len(sublist) for sublist in lyrics)
    payload = {
        "lyrics": lyrics,
        "lines": lines,
        "bpm": bpm,
        "voice": voices[0],
        "backing_track": backing_track,
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
    return str(freestyle["mix_url"])


if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()
