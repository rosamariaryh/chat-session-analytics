import os

from dotenv import load_dotenv

from llm_wrappers.gemini_client import GeminiClient
from llm_wrappers.openrouter_client import OpenRouterClient

from prompts.prompts_1 import (
    BATCH_METRICS_SCHEMA,
    BATCH_METRICS_JSON_SCHEMA,
)

load_dotenv()


def get_llm_client():
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "gemini":
        return GeminiClient()

    if provider == "openrouter":
        return OpenRouterClient()

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {provider}"
    )


def get_batch_schema():
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "gemini":
        return BATCH_METRICS_SCHEMA

    if provider == "openrouter":
        return BATCH_METRICS_JSON_SCHEMA

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {provider}"
    )