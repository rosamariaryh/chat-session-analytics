"""
Wrapper around the OpenRouter API for structured-output calls.

Provides the same basic interface as GeminiClient so the analysis
pipeline can switch LLM providers without changing the rest of
the application.

WORK IN PROGRESS
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "openrouter/free"


class OpenRouterClient:
    """Wraps an OpenAI-compatible OpenRouter client."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY environment variable is not set, "
                "and no api_key was passed explicitly."
            )

        self.model = (
            model
            or os.getenv("OPENROUTER_MODEL")
            or DEFAULT_MODEL
        )

        self._client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    @staticmethod
    def _parse_json(content: str) -> dict:
        """
        Parse JSON returned by the model.

        Handles both normal JSON and JSON wrapped in Markdown
        code fences.
        """

        content = content.strip()

        # Normal JSON.
        try:
            return json.loads(content)

        except json.JSONDecodeError:
            pass

        # JSON wrapped in Markdown code fences.
        match = re.search(
            r"```(?:json)?\s*(.*?)\s*```",
            content,
            re.DOTALL | re.IGNORECASE,
        )

        if match:
            try:
                return json.loads(match.group(1))

            except json.JSONDecodeError as exc:
                raise ValueError(
                    "OpenRouter returned invalid JSON inside a "
                    "Markdown code fence:\n"
                    f"{content}"
                ) from exc

        raise ValueError(
            "OpenRouter returned invalid JSON:\n"
            f"{content}"
        )

    @staticmethod
    def _get_message(response: Any) -> Any:
        """
        Safely extract the first response message.

        OpenRouter can occasionally return a response without choices,
        so don't assume response.choices[0] exists.
        """

        choices = getattr(response, "choices", None)

        if not choices:
            print("\n--- OPENROUTER RESPONSE HAD NO CHOICES ---")
            print(response)
            print("--- END RESPONSE ---\n")

            raise ValueError(
                "OpenRouter returned no choices."
            )

        message = getattr(choices[0], "message", None)

        if message is None:
            print("\n--- OPENROUTER RESPONSE HAD NO MESSAGE ---")
            print(response)
            print("--- END RESPONSE ---\n")

            raise ValueError(
                "OpenRouter returned no message."
            )

        return message

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        model: str | None = None,
        temperature: float = 0,
    ) -> str:
        """Send a simple text request to OpenRouter."""

        model_name = model or self.model

        messages = []

        if system_instruction:
            messages.append(
                {
                    "role": "system",
                    "content": system_instruction,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": prompt,
            }
        )

        response = self._client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
        )

        message = self._get_message(response)
        content = message.content

        if content is None:
            choices = getattr(response, "choices", [])
            finish_reason = (
                choices[0].finish_reason
                if choices
                else None
            )

            raise ValueError(
                f"OpenRouter returned no content. "
                f"finish_reason={finish_reason}, "
                f"message={message}"
            )

        if not content.strip():
            raise ValueError(
                "OpenRouter returned an empty response."
            )

        return content

    def generate_structured(
        self,
        prompt: str,
        system_instruction: str,
        schema: dict[str, Any],
        model: str | None = None,
        temperature: float = 0,
    ) -> dict:
        """Send a prompt and request a structured JSON response."""

        model_name = model or self.model

        messages = [
            {
                "role": "system",
                "content": system_instruction,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        response = self._client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=temperature,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "session_metrics",
                    "strict": True,
                    "schema": schema,
                },
            },
        )

        print(
            f"Requested model: {model_name}"
        )

        print(
            f"Actual OpenRouter model: "
            f"{getattr(response, 'model', None)}"
        )

        message = self._get_message(response)
        content = message.content

        if content is None:
            choices = getattr(response, "choices", [])
            finish_reason = (
                choices[0].finish_reason
                if choices
                else None
            )

            print("\n--- OPENROUTER RESPONSE HAD NO CONTENT ---")
            print(response)
            print("--- END RESPONSE ---\n")

            raise ValueError(
                f"OpenRouter returned no content. "
                f"finish_reason={finish_reason}"
            )

        if not content.strip():
            raise ValueError(
                "OpenRouter returned an empty response."
            )

        return self._parse_json(content)