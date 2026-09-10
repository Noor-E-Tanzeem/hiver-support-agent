import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-20b")


if LLM_PROVIDER != "groq":
    raise ValueError(
        f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. "
        "Currently supported: groq"
    )


api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError(
        "GROQ_API_KEY is not set. "
        "Copy .env.example to .env and add your API key."
    )


client = Groq(api_key=api_key)
