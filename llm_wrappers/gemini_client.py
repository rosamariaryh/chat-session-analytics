"""
Wrapper around the Gemini API for structured-output calls.

Handles:
- Gemini client creation
- model configuration
- structured JSON generation
- retries for transient API failures
"""

from __future__ import annotations

import json
import os
import random
import re
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEFAULT_MODEL = "gemini-3.5-flash-lite"


class GeminiClient:
    """Wraps a genai.Client with retrying structured-output calls."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        api_key = api_key or os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY environment variable is not set, "
                "and no api_key was passed explicitly."
            )

        self.model = (
                model
                or os.getenv("GEMINI_MODEL_NAME")
                or DEFAULT_MODEL
        )

        self.fallback_model = os.getenv(
            "GEMINI_FALLBACK_MODEL"
        )

        self._client = genai.Client(api_key=api_key)

    @staticmethod
    def _is_retryable(exc: Exception) -> bool:
        """Return True for transient API errors."""

        status_code = getattr(exc, "status_code", None)

        return status_code in {
            408,
            429,
            500,
            502,
            503,
            504,
        }

    @staticmethod
    def _is_model_overloaded(exc: Exception) -> bool:
        """Return True when Gemini reports that the model is overloaded."""

        status_code = getattr(exc, "status_code", None)

        return status_code == 503

    @staticmethod
    def _get_retry_delay(
        exc: Exception,
        attempt: int,
    ) -> float:
        """
        Get Google's suggested retry delay when available.

        Falls back to exponential backoff with jitter.
        """

        message = str(exc)

        match = re.search(
            r"retry in ([\d.]+)s",
            message,
            re.IGNORECASE,
        )

        if match:
            return float(match.group(1)) + random.uniform(0, 1)

        base_delay = min(2**attempt, 60)

        return base_delay + random.uniform(0, 1)

    def _generate_structured_once(
            self,
            prompt: str,
            system_instruction: str,
            schema: types.Schema,
            model_name: str,
            temperature: float,
    ) -> dict:
        """Make one structured Gemini API request."""

        response = self._client.models.generate_content(
            model=model_name,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(
                            text=prompt
                        )
                    ],
                )
            ],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=temperature,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty response."
            )

        return json.loads(response.text)

    def generate_structured(
            self,
            prompt: str,
            system_instruction: str,
            schema: types.Schema,
            model: str | None = None,
            temperature: float = 0,
            max_retries: int | None = None,
    ) -> dict:
        """
        Send a prompt to Gemini and return parsed JSON.

        Retries transient API errors.

        If the primary model returns 503 UNAVAILABLE after all retries,
        optionally switches to the configured fallback model.
        """

        primary_model = model or self.model

        if max_retries is None:
            max_retries = int(
                os.getenv("GEMINI_MAX_RETRIES", "3")
            )

        models_to_try = [primary_model]

        if (
                self.fallback_model
                and self.fallback_model != primary_model
        ):
            models_to_try.append(self.fallback_model)

        last_exc: Exception | None = None

        for model_index, model_name in enumerate(models_to_try):

            for attempt in range(max_retries + 1):

                try:
                    return self._generate_structured_once(
                        prompt=prompt,
                        system_instruction=system_instruction,
                        schema=schema,
                        model_name=model_name,
                        temperature=temperature,
                    )

                except Exception as exc:
                    last_exc = exc

                    # Never retry non-transient errors.
                    if not self._is_retryable(exc):
                        raise

                    # If the model is overloaded, retry it first.
                    if self._is_model_overloaded(exc):

                        if attempt < max_retries:
                            wait_seconds = self._get_retry_delay(
                                exc,
                                attempt,
                            )

                            print(
                                f"  Model {model_name} is overloaded "
                                f"(attempt {attempt + 1}/{max_retries}). "
                                f"Retrying in {wait_seconds:.1f}s..."
                            )

                            time.sleep(wait_seconds)
                            continue

                        # Primary model exhausted its retries.
                        # Try the fallback instead.
                        if model_index < len(models_to_try) - 1:
                            fallback_model = models_to_try[
                                model_index + 1
                                ]

                            print(
                                f"  Model {model_name} is still overloaded. "
                                f"Falling back to {fallback_model}."
                            )

                            break

                        raise

                    # Other transient errors, e.g. 429.
                    if attempt >= max_retries:
                        raise

                    wait_seconds = self._get_retry_delay(
                        exc,
                        attempt,
                    )

                    print(
                        f"  Gemini transient error on "
                        f"{model_name} "
                        f"(attempt {attempt + 1}/{max_retries}). "
                        f"Retrying in {wait_seconds:.1f}s..."
                    )

                    time.sleep(wait_seconds)

        raise last_exc  # pragma: no cover