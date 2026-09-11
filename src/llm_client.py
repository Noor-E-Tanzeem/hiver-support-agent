import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


LLM_MODEL = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-20b",
)


api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY is not set. "
        "Copy .env.example to .env and add your API key."
    )


client = Groq(api_key=api_key)


def generate(messages, json_mode=True, max_tokens=1024):
    """
    Generate a response using the configured Groq model.

    Takes messages in the standard chat format:
    [
        {"role": "system", "content": "..."},
        {"role": "user", "content": "..."}
    ]

    Returns the raw text response.
    """

    kwargs = dict(
        model=LLM_MODEL,
        temperature=0,
        max_completion_tokens=max_tokens,
        messages=messages,
    )

    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)

    return response.choices[0].message.content


if __name__ == "__main__":
    print("LLM client loaded successfully.")
    print("Provider: Groq")
    print(f"Model: {LLM_MODEL}")
    print("API call intentionally not made.")
