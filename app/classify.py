# classify.py
import time
import random

from llm_wrappers.client import get_llm_client

from .config import MAX_RETRIES, PROVIDER
from .rate_limiter import rate_limiter
from prompts.prompts_updated import (
    SYSTEM_INSTRUCTIONS,
    BATCH_METRICS_SCHEMA,
    BATCH_METRICS_JSON_SCHEMA,
    build_batch_user_prompt,
)

# Initialized once, shared across all threads/calls
client = get_llm_client()


def classify_batch(
    batch_index: int,
    batch: list[tuple[int, dict]],
) -> tuple[int, list[tuple[int, dict]]]:
    """Classify one batch of sessions, with retries for transient errors."""

    prompt = build_batch_user_prompt(batch)

    if PROVIDER == "openrouter":
        schema = BATCH_METRICS_JSON_SCHEMA
    else:
        schema = BATCH_METRICS_SCHEMA

    last_exc: Exception | None = None

    for attempt in range(MAX_RETRIES):
        rate_limiter.wait()

        try:
            response = client.generate_structured(
                prompt=prompt,
                system_instruction=SYSTEM_INSTRUCTIONS,
                schema=schema,
            )

            if isinstance(response, dict):
                classifications = response.get("classifications")
            elif isinstance(response, list):
                classifications = response
            else:
                raise ValueError(
                    f"Batch {batch_index + 1}: unexpected response type: "
                    f"{type(response).__name__}"
                )

            if not isinstance(classifications, list):
                raise ValueError(
                    f"Batch {batch_index + 1}: expected classifications "
                    f"to be a list, got {type(classifications).__name__}"
                )

            if len(classifications) != len(batch):
                raise ValueError(
                    f"Batch {batch_index + 1}: returned "
                    f"{len(classifications)} classifications for "
                    f"{len(batch)} sessions."
                )

            results = []

            for (session_index, session), classification in zip(
                batch,
                classifications,
            ):
                session["classification"] = classification
                results.append((session_index, session))

            return batch_index, results

        except Exception as exc:
            last_exc = exc

            if attempt == MAX_RETRIES - 1:
                break

            is_rate_limit = "429" in str(exc) or "rate" in str(exc).lower()

            backoff = 2 * (2 ** attempt) + random.uniform(0, 2)
            if is_rate_limit:
                backoff += 10

            print(
                f"Batch {batch_index + 1}: attempt {attempt + 1}/"
                f"{MAX_RETRIES} failed ({exc}). "
                f"Retrying in {backoff:.1f}s..."
            )

            time.sleep(backoff)

    raise last_exc