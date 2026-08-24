"""
Add message counts and dataset summaries to validated chat sessions.

Usage:
    uv run python app/preprocess.py data/processed/<timestamp>_validated_sessions.jsonl
"""

from __future__ import annotations

from collections import Counter


def process_session(session: dict) -> dict:
    """Add message counts and interaction complexity to a session."""

    messages = session["messages"]

    role_counts = Counter(
        message["role"]
        for message in messages
    )

    user_message_count = role_counts["user"]
    assistant_message_count = role_counts["assistant"]

    session["message_count"] = len(messages)
    session["user_message_count"] = user_message_count
    session["assistant_message_count"] = assistant_message_count

    if (
        user_message_count == 1
        and assistant_message_count == 1
    ):
        session["interaction_complexity"] = "simple"
    elif (
        user_message_count >= 5
        and assistant_message_count >= 5
    ):
        session["interaction_complexity"] = "deep_work"
    else:
        session["interaction_complexity"] = "multi_turn"

    return session
