import os

import openai

openai.api_key = os.environ.get("OPENAI_API_KEY")


def make_lyrics(text: str) -> str:
    model = "gpt-4"  # "gpt-3.5-turbo" or "gpt-4"
    system_prompt = (
        "Output is an array of arrays of strings in JSON format. "
        "Lines of verse, chorus, and outro are packed in an internal array."
    )
    prompt = f"Convert the message to a rap song. \n\n```{text}```"

    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )
    return response["choices"][0]["message"]["content"]


if __name__ == "__main__":
    text = """Hello Engineers,
Please let me announce that starting from July 1,
the Data Science Group belongs to our Engineering Department
(they belonged to the Product Division until June). 
"""
    print(make_lyrics(text))
