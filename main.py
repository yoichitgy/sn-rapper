import json
import logging
import os

import requests

# Logging
logging.basicConfig(
    format="[%(asctime)s][%(levelname)s] %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


# Environment variables
UBERDUCK_API_KEY = os.environ.get("UBERDUCK_API_KEY")
UBERDUCK_SECRET_KEY = os.environ.get("UBERDUCK_SECRET_KEY")
if not UBERDUCK_API_KEY or not UBERDUCK_SECRET_KEY:
    raise ValueError(
        "Please set UBERDUCK_API_KEY and UBERDUCK_SECRET_KEY environment variables"
    )
UBERDUCK_AUTH = (UBERDUCK_API_KEY, UBERDUCK_SECRET_KEY)


def freestyle() -> None:
    lyrics = [
        [
            "rap cat, hell make you clap",
            "hes got the hottest beats and the softest fur",
            "nothing to laugh at",
            "riding with the rap cat",
        ]
    ]
    voices = ["jsxi", "relikk"]
    backing_tracks = [
        ("2c3adf4e-c2b9-4419-94ee-f2f61446d07f", 105),  # Nike - Futile
        ("5fff1ec6-8736-4992-a842-8b78d37b8a8a", 90),  # Downtown - Barré
    ]

    backing_track = backing_tracks[0][0]
    bpm = backing_tracks[0][1]
    lines = len(lyrics[0])
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
    logger.info(f"URL: {freestyle['mix_url']}")


def voices() -> None:
    url = "https://api.uberduck.ai/voices"
    headers = {"accept": "application/json"}
    params = {"mode": "tts-basic"}
    response = requests.get(url, headers=headers, params=params)
    print(response.text)


def backing_tracks() -> None:
    url = "https://api.uberduck.ai/reference-audio/backing-tracks"
    headers = {"accept": "application/json"}
    response = requests.get(url, headers=headers)
    print(response.text)


if __name__ == "__main__":
    freestyle()
