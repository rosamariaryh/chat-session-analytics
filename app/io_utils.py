import csv
import json
from pathlib import Path
from collections import Counter
from prompts.prompts_updated import (
    TOPIC_TAXONOMY,
    USER_INTENT_TAXONOMY,
)


# ---------------------------------------------------------------------------
# CSV helper
# ---------------------------------------------------------------------------

def append_session_csv(
    output_path: Path,
    results: list[tuple[int, dict]],
) -> None:
    """
    Append completed sessions to a BI-friendly CSV.

    One row represents one session.

    Nested messages are intentionally excluded because the JSONL file
    is the canonical source for the full conversation.
    """

    fieldnames = [
        "session_id",
        "user_id",
        "user_tier",
        "platform",
        "attachment_type",
        "has_attachment",
        "message_count",
        "user_message_count",
        "assistant_message_count",
        "interaction_complexity",
        "language",
        "primary_topic",
        "user_intent",
        "user_goal",
        "task_outcome",
        "abandonment",
        "follow_up_needed",
    ]

    file_exists = output_path.exists()

    with output_path.open(
        "a",
        encoding="utf-8",
        newline="",
    ) as outfile:

        writer = csv.DictWriter(
            outfile,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )

        if not file_exists:
            writer.writeheader()

        for index, session in results:

            classification = session.get(
                "classification",
                {},
            )

            if not isinstance(classification, dict):
                classification = {}

            writer.writerow({
                "session_id": session.get(
                    "session_id",
                    "",
                ),
                "user_id": session.get(
                    "user_id",
                    "",
                ),
                "user_tier": session.get(
                    "user_tier",
                    "",
                ),
                "platform": session.get(
                    "platform",
                    "",
                ),
                "attachment_type": session.get(
                    "attachment_type",
                    "",
                ),
                "has_attachment": session.get(
                    "has_attachment",
                    "",
                ),
                "message_count": session.get(
                    "message_count",
                    "",
                ),
                "user_message_count": session.get(
                    "user_message_count",
                    "",
                ),
                "assistant_message_count": session.get(
                    "assistant_message_count",
                    "",
                ),
                "interaction_complexity": session.get(
                    "interaction_complexity",
                    "",
                ),
                "language": classification.get(
                    "language",
                    "",
                ),
                "primary_topic": classification.get(
                    "primary_topic",
                    "",
                ),
                "user_intent": classification.get(
                    "user_intent",
                    "",
                ),
                "user_goal": classification.get(
                    "user_goal",
                    "",
                ),
                "task_outcome": classification.get(
                    "task_outcome",
                    "",
                ),
                "abandonment": classification.get(
                    "abandonment",
                    "",
                ),
                "follow_up_needed": classification.get(
                    "follow_up_needed",
                    "",
                ),
            })

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_sessions(
    input_path: Path,
) -> list[dict]:
    """Load sessions from a JSONL file."""

    sessions = []

    with input_path.open(
        "r",
        encoding="utf-8",
    ) as infile:

        for line in infile:
            if not line.strip():
                continue

            sessions.append(
                json.loads(line)
            )

    return sessions

# ---------------------------------------------------------------------------
# Checkpointing
# ---------------------------------------------------------------------------

def load_completed_sessions(
    output_path: Path,
) -> dict[int, dict]:
    """
    Load already-completed sessions.

    Uses _classification_index to identify the original
    position of each session.
    """

    completed = {}

    if not output_path.exists():
        return completed

    with output_path.open(
        "r",
        encoding="utf-8",
    ) as infile:

        for line in infile:
            if not line.strip():
                continue

            session = json.loads(line)

            index = session.get(
                "_classification_index"
            )

            if index is not None:
                completed[index] = session

    return completed


def append_results(
    output_path: Path,
    results: list[tuple[int, dict]],
) -> None:
    """
    Append completed classifications immediately.

    This makes the pipeline resumable if the process crashes.
    """

    with output_path.open(
        "a",
        encoding="utf-8",
    ) as outfile:

        for index, session in results:
            session["_classification_index"] = index

            outfile.write(
                json.dumps(
                    session,
                    ensure_ascii=False,
                )
                + "\n"
            )

# ---------------------------------------------------------------------------
# Classification summaries
# ---------------------------------------------------------------------------

def build_classification_summary(
    completed: dict[int, dict],
) -> dict:
    """
    Build dataset-level counts from the final merged sessions.

    Counts both preprocessing information and LLM classification
    information.
    """

    platform_count = Counter()
    user_tier_count = Counter()
    attachment_type_count = Counter()
    interaction_complexity_count = Counter()

    language_count = Counter()

    primary_topic_count = Counter(
        {
            primary_topic: 0
            for primary_topic in TOPIC_TAXONOMY
        }
    )

    user_intent_count = Counter(
        {
            user_intent: 0
            for user_intent in USER_INTENT_TAXONOMY
        }
    )

    task_outcome_count = Counter()
    abandonment_count = Counter()
    follow_up_needed_count = Counter()

    for session in completed.values():

        # Preprocessing information
        platform_count[
            session.get("platform", "unknown")
        ] += 1

        user_tier_count[
            session.get("user_tier", "unknown")
        ] += 1

        attachment_type_count[
            session.get("attachment_type", "unknown")
        ] += 1

        interaction_complexity_count[
            session.get(
                "interaction_complexity",
                "unknown",
            )
        ] += 1

        # Classification information
        classification = session.get(
            "classification",
            {},
        )

        if not isinstance(classification, dict):
            classification = {}

        language_count[
            classification.get("language", "unknown")
        ] += 1

        primary_topic = classification.get(
            "primary_topic",
            "unknown",
        )

        primary_topic_count[primary_topic] += 1

        user_intent = classification.get(
            "user_intent",
            "unknown",
        )

        user_intent_count[user_intent] += 1

        task_outcome_count[
            classification.get("task_outcome", "unknown")
        ] += 1

        abandonment_count[
            classification.get("abandonment", "unknown")
        ] += 1

        follow_up_needed_count[
            classification.get(
                "follow_up_needed",
                "unknown",
            )
        ] += 1

    return {
        "platform_count": dict(platform_count),
        "user_tier_count": dict(user_tier_count),
        "attachment_type_count": dict(attachment_type_count),
        "interaction_complexity_count": dict(
            interaction_complexity_count
        ),
        "language_count": dict(language_count),
        "primary_topic_count": dict(
            primary_topic_count
        ),
        "user_intent_count": dict(
            user_intent_count
        ),
        "task_outcome_count": dict(
            task_outcome_count
        ),
        "abandonment_count": dict(
            abandonment_count
        ),
        "follow_up_needed_count": dict(
            follow_up_needed_count
        ),
    }


def save_classification_summary(
    summary_path: Path,
    completed: dict[int, dict],
) -> None:
    """Build and save the current classification summary."""

    summary = build_classification_summary(
        completed,
    )

    with summary_path.open(
        "w",
        encoding="utf-8",
    ) as outfile:

        json.dump(
            summary,
            outfile,
            indent=2,
            ensure_ascii=False,
        )

        outfile.write("\n")

# ---------------------------------------------------------------------------
# Clean output
# ---------------------------------------------------------------------------

def remove_internal_classification_fields(
    session: dict,
) -> dict:
    """Remove LLM grounding fields that should not appear in output."""

    classification = session.get("classification")

    if isinstance(classification, dict):
        classification.pop("outcome_explanation", None)
        classification.pop("outcome_confidence", None)

    return session