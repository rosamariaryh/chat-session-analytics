"""
Load and validate raw chat-session JSONL data.

This step:
- validates required session fields
- rejects invalid sessions
- reports missing/null fields
- reports duplicate session IDs
- saves valid sessions for the preprocessing step

Usage:
    uv run python app/load_data.py ../data/raw/mock_chat_sessions_150.jsonl
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_SESSION_FIELDS = {
    "session_id",
    "user_id",
    "user_tier",
    "platform",
    "attachment_type",
    "has_attachment",
    "messages",
}

REQUIRED_MESSAGE_FIELDS = {"role", "content"}
VALID_ROLES = {"user", "assistant"}


def load_jsonl(
    path: str | Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load JSON objects and keep malformed lines for quality reporting."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    sessions = []
    invalid_records = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                invalid_records.append(
                    {
                        "line_number": line_number,
                        "reason": "invalid JSON",
                        "error": str(exc),
                        "raw_line": line,
                    }
                )
                continue

            if not isinstance(record, dict):
                invalid_records.append(
                    {
                        "line_number": line_number,
                        "reason": "JSON value is not an object",
                        "raw_line": line,
                    }
                )
                continue

            sessions.append(record)

    return sessions, invalid_records


def validate_session(
    session: dict[str, Any],
    seen_session_ids: set[str],
) -> list[str]:
    """Return validation errors for a session."""
    errors = []

    # Required keys
    missing = REQUIRED_SESSION_FIELDS - session.keys()

    if missing:
        errors.append(
            f"missing required fields: {', '.join(sorted(missing))}"
        )

    # Required values cannot be null
    null_fields = [
        field
        for field in REQUIRED_SESSION_FIELDS
        if field in session and session[field] is None
    ]

    if null_fields:
        errors.append(
            f"null required fields: {', '.join(sorted(null_fields))}"
        )

    # session_id is required for duplicate detection
    if "session_id" in session and session["session_id"] is not None:
        session_id = str(session["session_id"])

        if session_id in seen_session_ids:
            errors.append("duplicate session_id")

    # Messages
    messages = session.get("messages")

    if messages is None:
        errors.append("missing messages")
    elif not isinstance(messages, list):
        errors.append("messages must be a list")
    elif not messages:
        errors.append("missing messages")

    # Validate individual messages when possible
    if isinstance(messages, list):
        for index, message in enumerate(messages, start=1):
            if not isinstance(message, dict):
                errors.append(f"message {index} must be an object")
                continue

            missing_fields = REQUIRED_MESSAGE_FIELDS - message.keys()

            if missing_fields:
                errors.append(
                    f"message {index} missing fields: "
                    f"{', '.join(sorted(missing_fields))}"
                )
                continue

            if message["role"] not in VALID_ROLES:
                errors.append(
                    f"message {index} has invalid role "
                    f"'{message['role']}'"
                )

            if not isinstance(message["content"], str):
                errors.append(
                    f"message {index} content must be a string"
                )

    return errors


def validate_sessions(
    sessions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """
    Validate all sessions.

    Returns:
        valid_sessions
        rejected_sessions
        quality_counts
    """
    missing_required = {
        field: 0 for field in REQUIRED_SESSION_FIELDS
    }

    null_required = {
        field: 0 for field in REQUIRED_SESSION_FIELDS
    }

    duplicate_session_ids = 0
    missing_messages = 0

    valid_sessions = []
    rejected_sessions = []
    seen_session_ids: set[str] = set()

    for index, session in enumerate(sessions, start=1):
        # Track missing fields
        missing = REQUIRED_SESSION_FIELDS - session.keys()

        for field in missing:
            missing_required[field] += 1

        # Track null fields
        null_fields = [
            field
            for field in REQUIRED_SESSION_FIELDS
            if field in session and session[field] is None
        ]

        for field in null_fields:
            null_required[field] += 1

        # Track missing/empty messages
        messages = session.get("messages")

        if (
            "messages" not in session
            or messages is None
            or (isinstance(messages, list) and not messages)
        ):
            missing_messages += 1

        # Validate session
        errors = validate_session(
            session,
            seen_session_ids,
        )

        # Track session IDs
        if "session_id" in session and session["session_id"] is not None:
            session_id = str(session["session_id"])

            if session_id in seen_session_ids:
                duplicate_session_ids += 1
            else:
                seen_session_ids.add(session_id)

        # Reject or accept
        if errors:
            rejected_sessions.append(
                {
                    "session_number": index,
                    "session_id": session.get("session_id"),
                    "reasons": errors,
                    "session": session,
                }
            )
        else:
            valid_sessions.append(session)

    quality_counts = {
        "missing_required_fields": missing_required,
        "null_required_fields": null_required,
        "missing_messages": missing_messages,
        "duplicate_session_id": duplicate_session_ids,
    }

    return valid_sessions, rejected_sessions, quality_counts


def load_and_validate(
    path: str | Path,
) -> list[dict[str, Any]]:
    """
    Load raw JSONL and return only validated sessions.

    This function is used by preprocess.py when it needs the
    validated session data.
    """
    sessions, _ = load_jsonl(path)

    valid_sessions, _, _ = validate_sessions(sessions)

    return valid_sessions
