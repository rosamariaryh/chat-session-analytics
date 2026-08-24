"""
Prompt and taxonomy definitions for session classification.

Keeping this separate from the pipeline script means the taxonomy, schema,
and system instructions can be edited/reviewed without touching the API
call logic, retries, or CLI plumbing.
"""

import json
from google.genai import types

# ---------------------------------------------------------------------------
# Taxonomy
# ---------------------------------------------------------------------------

# The dictionary keys are the exact values the LLM is allowed to output.
# The descriptions are classification guidance shown to the LLM.
TOPIC_TAXONOMY = {
    "factual_qa": (
        "Single lookup-style fact, no personal context or ongoing task."
    ),
    "document_analysis": (
        "Task is performed on an attached file "
        "(summarize, clean, extract, analyze)."
    ),
    "image_editing": (
        "Attachment or request involves creating or modifying an image."
    ),
    "coding_tech": (
        "Conceptual or advisory question about code, AI, or tech products "
        "(not an attached file)."
    ),
    "health_wellness": (
        "Question about physical body, symptoms, or medication, "
        "not emotional state."
    ),
    "mental_wellbeing": (
        "About the person's internal state "
        "(mood, sleep, focus, motivation) with no other domain causing it."
    ),
    "relationships_social": (
        "Situation involving friends, dating, or social etiquette."
    ),
    "parenting_family": (
        "Situation involving children or family members."
    ),
    "career_workplace": (
        "Situation or task tied to a job, coworker, or work task."
    ),
    "finance_legal": (
        "Money management or a legal or contractual question."
    ),
    "travel_recommendations": (
        "Trip planning or location-specific logistics."
    ),
    "learning_self_improvement": (
        "Building a skill or habit, not driven by a work, family, "
        "or relationship situation."
    ),
    "chitchat": (
        "Greeting, test input, or no real request present."
    ),
    "other": (
        "Doesn't fit any category above."
    ),
}

# Exact values that are allowed in the structured LLM output.
TOPIC_TAXONOMY_VALUES = list(TOPIC_TAXONOMY.keys())


TASK_OUTCOMES = [
    "completed",
    "partially_completed",
    "failed",
    "unclear",
    "not_applicable",
]


# ---------------------------------------------------------------------------
# Prompt-friendly taxonomy definitions
# ---------------------------------------------------------------------------

TOPIC_DEFINITIONS = "\n".join(
    f"- {topic}: {description}"
    for topic, description in TOPIC_TAXONOMY.items()
)




# ---------------------------------------------------------------------------
# Gemini response schema
# ---------------------------------------------------------------------------

METRICS_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "language": types.Schema(
            type=types.Type.STRING,
            description=(
                "The primary language used by the user in the conversation. "
                "Use a standard language name such as English, Spanish, "
                "French, German, etc."
            ),
        ),
        "primary_topic": types.Schema(
            type=types.Type.STRING,
            enum=list(TOPIC_TAXONOMY.keys()),
            description=(
                "The single best primary topic of the conversation."
            ),
        ),
        "user_goal": types.Schema(
            type=types.Type.STRING,
            description=(
                "A concise description of what the user was ultimately "
                "trying to accomplish. Do not merely repeat their first "
                "question."
            ),
        ),
        "task_outcome": types.Schema(
            type=types.Type.STRING,
            enum=TASK_OUTCOMES,
            description=(
                "Whether the user's goal was completed, partially completed, "
                "failed, unclear, or not applicable."
            ),
        ),
        "outcome_confidence": types.Schema(
            type=types.Type.NUMBER,
            description=(
                "Confidence in the task_outcome classification, from 0.0 "
                "to 1.0."
            ),
        ),
        "outcome_explanation": types.Schema(
            type=types.Type.STRING,
            description=(
                "A short explanation grounded in evidence from the "
                "conversation for why the selected task outcome is correct."
            ),
        ),
        "abandonment": types.Schema(
            type=types.Type.BOOLEAN,
            description=(
                "True if the user appears to have stopped pursuing their "
                "goal before reaching a satisfactory resolution."
            ),
        ),
        "follow_up_needed": types.Schema(
            type=types.Type.BOOLEAN,
            description=(
                "True if additional user information, action, or interaction "
                "is required to complete the user's goal."
            ),
        ),
    },
    required=[
        "language",
        "primary_topic",
        "user_goal",
        "task_outcome",
        "outcome_confidence",
        "outcome_explanation",
        "abandonment",
        "follow_up_needed",
    ],
)

BATCH_METRICS_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "classifications": types.Schema(
            type=types.Type.ARRAY,
            items=METRICS_SCHEMA,
            description=(
                "One classification object for every session in the input. "
                "The order must exactly match the order of the sessions."
            ),
        ),
    },
    required=["classifications"],
)

# ---------------------------------------------------------------------------
# Model-agnostic response schema
# ---------------------------------------------------------------------------

METRICS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "language": {
            "type": "string",
            "description": (
                "The primary language used by the user."
            ),
        },

        "primary_topic": {
            "type": "string",
            "enum": TOPIC_TAXONOMY,
        },

        "user_goal": {
            "type": "string",
        },

        "task_outcome": {
            "type": "string",
            "enum": TASK_OUTCOMES,
        },

        "outcome_confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
        },

        "outcome_explanation": {
            "type": "string",
        },

        "abandonment": {
            "type": "boolean",
        },

        "follow_up_needed": {
            "type": "boolean",
        },
    },

    "required": [
        "language",
        "primary_topic",
        "user_goal",
        "task_outcome",
        "outcome_confidence",
        "outcome_explanation",
        "abandonment",
        "follow_up_needed",
    ],

    "additionalProperties": False,
}

BATCH_METRICS_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "classifications": {
            "type": "array",
            "items": METRICS_JSON_SCHEMA,
            "description": (
                "One classification object for every session in the input. "
                "The order must exactly match the order of the sessions."
            ),
        },
    },
    "required": ["classifications"],
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# System instructions
# ---------------------------------------------------------------------------

SYSTEM_INSTRUCTIONS = f"""
You are analyzing chatbot sessions for a product analytics pipeline.

Your job is to classify each conversation into a structured schema that will
later be used for aggregation, dashboards, and product/engineering analysis.

IMPORTANT PRINCIPLES:

1. Base your decisions only on the conversation provided.
2. Do not invent information that is not supported by the transcript.
3. Prefer "unclear" for task_outcome when the evidence is insufficient.
4. outcome_confidence represents how strongly the conversation supports your
   task_outcome judgment, not how confident you are in your general answer.
5. user_goal should describe what the user was trying to accomplish, not simply
   quote their first message.
6. primary_topic MUST be exactly one of the allowed taxonomy values.
7. Use the topic definitions below to decide which category best fits.
8. Output the taxonomy VALUE, not the topic description.
9. Keep outcome_explanation short and evidence-based.
10. Do not infer abandonment merely because the transcript ends. Consider
    whether the user's goal was already satisfactorily completed.
11. follow_up_needed means that additional information, action, or interaction
    is actually needed to accomplish the user's goal.

PRIMARY TOPIC TAXONOMY:

These are the only valid values for primary_topic:

{", ".join(TOPIC_TAXONOMY_VALUES)}

TOPIC DEFINITIONS:

Use these definitions to determine the best category. The definition is
classification guidance; do NOT output the definition itself.

{TOPIC_DEFINITIONS}

TASK OUTCOME VALUES:
{", ".join(TASK_OUTCOMES)}

DEFINITIONS:

- completed:
  The user's goal was successfully achieved or there is strong evidence that
  the requested task was completed.

- partially_completed:
  Some meaningful progress was made, but the user's goal was not fully achieved.

- failed:
  The conversation clearly did not accomplish the user's goal.

- unclear:
  There is insufficient evidence to determine whether the goal was achieved.

- not_applicable:
  There is no meaningful task outcome to evaluate.

ABANDONMENT:
Set abandonment=true when the user appears to stop pursuing their goal before
a satisfactory resolution. Do NOT mark abandonment=true simply because the
conversation ends naturally after a successful answer.

FOLLOW-UP:
Set follow_up_needed=true when the user would need to provide more information,
take another action, or continue interacting in order to achieve their goal.
"""


def build_user_prompt(session: dict) -> str:
    """
    Convert one session object into a prompt.

    We serialize the complete session rather than trying to reconstruct the
    transcript here. This means the script can work with your existing JSON
    structure without making assumptions about the exact field names.
    """

    session_json = json.dumps(
        session,
        ensure_ascii=False,
        indent=2,
    )

    return f"""
Analyze the following chatbot session.

Return ONLY the structured JSON object matching the required schema.

For primary_topic, choose exactly one of the allowed taxonomy values. Use the
topic definitions in the system instructions as classification guidance, but
return only the taxonomy value.

SESSION:
{session_json}
"""

def build_batch_user_prompt(
    sessions: list[tuple[int, dict]],
) -> str:
    """
    Convert multiple sessions into one Gemini prompt.

    Each tuple contains:
        (original_session_index, session)
    """

    session_blocks = []

    for index, session in sessions:
        session_json = json.dumps(
            session,
            ensure_ascii=False,
            indent=2,
        )

        session_blocks.append(
            f"""
SESSION INDEX: {index}

{session_json}
"""
        )

    sessions_text = "\n".join(session_blocks)

    return f"""
Analyze all of the chatbot sessions below.

Return exactly ONE classification object for each session.

IMPORTANT:
- Return the classifications in exactly the same order as the sessions.
- Do not omit any session.
- Do not combine sessions.
- Do not add classifications for sessions that were not provided.
- Each classification must match the required schema.
- The first classification corresponds to the first session.
- The second classification corresponds to the second session.
- And so on.

SESSIONS:
{sessions_text}
"""