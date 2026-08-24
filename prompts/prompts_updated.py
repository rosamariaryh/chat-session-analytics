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


# ---------------------------------------------------------------------------
# User intent taxonomy
# ---------------------------------------------------------------------------

# User intent describes WHAT the user is trying to accomplish,
# while primary_topic describes WHAT the conversation is about.
#
# The dictionary keys are the exact values the LLM is allowed to output.
USER_INTENT_TAXONOMY = {
    "information_seeking": (
        "User wants a factual answer, definition, explanation, or "
        "lookup-style information."
    ),
    "advice_guidance": (
        "User wants practical guidance about what they should do, "
        "how they should approach a situation, or how to act."
    ),
    "decision_support": (
        "User is evaluating options, tradeoffs, or alternatives and wants "
        "help making a decision."
    ),
    "problem_solving": (
        "User has a specific problem, error, obstacle, or failure and wants "
        "help resolving it."
    ),
    "creation_generation": (
        "User wants new content, code, an image, document, plan, or other "
        "artifact created from scratch."
    ),
    "editing_rewriting": (
        "User provides existing content or an existing artifact and wants it "
        "rewritten, edited, improved, transformed, or corrected."
    ),
    "analysis_extraction": (
        "User wants existing information, text, files, images, or data "
        "analyzed, summarized, interpreted, classified, or extracted."
    ),
    "planning_recommendations": (
        "User wants a plan, itinerary, recommendations, or structured next "
        "steps for a future activity or goal."
    ),
    "learning_explanation": (
        "User wants to learn, understand, practice, or build knowledge or "
        "a skill through explanation or instruction."
    ),
    "emotional_support": (
        "User is seeking emotional support, reassurance, reflection, or help "
        "with an emotional or personal situation."
    ),
}

# Exact values that are allowed in the structured LLM output.
USER_INTENT_VALUES = list(
    USER_INTENT_TAXONOMY.keys()
)


# ---------------------------------------------------------------------------
# Task outcomes
# ---------------------------------------------------------------------------

TASK_OUTCOMES = [
    "completed",
    "partially_completed",
    "failed",
    "unclear",
    "not_applicable",
]


# ---------------------------------------------------------------------------
# Canonical field definitions
# ---------------------------------------------------------------------------
# These definitions are the single source of truth shared by all providers.
# Provider-specific schemas should reference these constants rather than
# maintaining their own copies of the classification guidance.

LANGUAGE_DEFINITION = (
    "The primary language used by the user in the conversation. "
    "Use a standard language name such as English, Spanish, French, German, etc."
)

#classification
PRIMARY_TOPIC_DEFINITION = (
    "The single best primary topic of the conversation. "
    "This describes WHAT the conversation is about."
)

#classification
USER_INTENT_DEFINITION = (
    "The primary thing the user is trying to accomplish in the conversation. "
    "This describes WHAT THE USER IS TRYING TO ACCOMPLISH, rather than what "
    "topic is being discussed."
)

#free text
USER_GOAL_DEFINITION = (
    "A concise description of the user's query. Use maximum 5 words."
)

TASK_OUTCOME_DEFINITION = (
    "Whether the user's goal was completed, partially completed, failed, "
    "unclear, or not applicable."
)

OUTCOME_CONFIDENCE_DEFINITION = (
    "Confidence in the task_outcome classification, from 0.0 to 1.0."
)

OUTCOME_EXPLANATION_DEFINITION = (
    "A short explanation grounded in evidence from the conversation for why "
    "the selected task outcome is correct."
)

ABANDONMENT_DEFINITION = (
    "True if the user appears to have stopped pursuing their goal before "
    "reaching a satisfactory resolution."
)

FOLLOW_UP_NEEDED_DEFINITION = (
    "True if additional user information, action, or interaction is required "
    "to complete the user's goal."
)


# ---------------------------------------------------------------------------
# Prompt-friendly taxonomy definitions
# ---------------------------------------------------------------------------

TOPIC_DEFINITIONS = "\n".join(
    f"- {topic}: {description}"
    for topic, description in TOPIC_TAXONOMY.items()
)

USER_INTENT_DEFINITIONS = "\n".join(
    f"- {intent}: {description}"
    for intent, description in USER_INTENT_TAXONOMY.items()
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
                LANGUAGE_DEFINITION
            ),
        ),
        "primary_topic": types.Schema(
            type=types.Type.STRING,
            enum=list(TOPIC_TAXONOMY.keys()),
            description=(
                PRIMARY_TOPIC_DEFINITION
            ),
        ),
        "user_intent": types.Schema(
            type=types.Type.STRING,
            enum=list(USER_INTENT_TAXONOMY.keys()),
            description=(
                USER_INTENT_DEFINITION
            ),
        ),
        "user_goal": types.Schema(
            type=types.Type.STRING,
            description=(
                USER_GOAL_DEFINITION
            ),
        ),
        "task_outcome": types.Schema(
            type=types.Type.STRING,
            enum=TASK_OUTCOMES,
            description=(
                TASK_OUTCOME_DEFINITION
            ),
        ),
        "outcome_confidence": types.Schema(
            type=types.Type.NUMBER,
            description=(
                OUTCOME_CONFIDENCE_DEFINITION
            ),
        ),
        "outcome_explanation": types.Schema(
            type=types.Type.STRING,
            description=(
                OUTCOME_EXPLANATION_DEFINITION
            ),
        ),
        "abandonment": types.Schema(
            type=types.Type.BOOLEAN,
            description=(
                ABANDONMENT_DEFINITION
            ),
        ),
        "follow_up_needed": types.Schema(
            type=types.Type.BOOLEAN,
            description=(
                FOLLOW_UP_NEEDED_DEFINITION
            ),
        ),
    },
    required=[
        "language",
        "primary_topic",
        "user_intent",
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
            "description": LANGUAGE_DEFINITION,
        },

        "primary_topic": {
            "type": "string",
            "enum": TOPIC_TAXONOMY_VALUES,
            "description": PRIMARY_TOPIC_DEFINITION,
        },

        "user_intent": {
            "type": "string",
            "enum": USER_INTENT_VALUES,
            "description": USER_INTENT_DEFINITION,
        },

        "user_goal": {
            "type": "string",
            "description": USER_GOAL_DEFINITION,
        },

        "task_outcome": {
            "type": "string",
            "enum": TASK_OUTCOMES,
            "description": TASK_OUTCOME_DEFINITION,
        },

        "outcome_confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": OUTCOME_CONFIDENCE_DEFINITION,
        },

        "outcome_explanation": {
            "type": "string",
            "description": OUTCOME_EXPLANATION_DEFINITION,
        },

        "abandonment": {
            "type": "boolean",
            "description": ABANDONMENT_DEFINITION,
        },

        "follow_up_needed": {
            "type": "boolean",
            "description": FOLLOW_UP_NEEDED_DEFINITION,
        },
    },

    "required": [
        "language",
        "primary_topic",
        "user_intent",
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

Your task is to classify each conversation into the required structured schema
for product analytics, dashboards, and product/engineering analysis.

IMPORTANT PRINCIPLES:

1. Base every classification only on the conversation provided.
2. Do not invent facts, intentions, outcomes, or attributes not supported by
   the conversation.
3. Classify the user's actual request and goal, not assumptions about what they
   might have wanted.
4. When evidence is insufficient, use "unclear" rather than guessing.
5. Keep free-text fields concise and evidence-based.
6. Use the controlled vocabularies exactly as defined. Do not create new
   category values.

PRIMARY TOPIC:

Choose exactly one value from:

{", ".join(TOPIC_TAXONOMY_VALUES)}

TOPIC DEFINITIONS:

{TOPIC_DEFINITIONS}

Primary topic describes WHAT the conversation is about.

USER INTENT:

Choose exactly one value from:

{", ".join(USER_INTENT_VALUES)}

USER INTENT DEFINITIONS:

{USER_INTENT_DEFINITIONS}

User intent describes WHAT THE USER IS TRYING TO ACCOMPLISH.

IMPORTANT DISTINCTION BETWEEN PRIMARY TOPIC AND USER INTENT:

Primary topic describes WHAT the conversation is about.
User intent describes WHAT the user is trying to accomplish.

Examples:

- "What are the symptoms of flu?"
  -> primary_topic: health_wellness
  -> user_intent: information_seeking

- "Should I see a doctor about these symptoms?"
  -> primary_topic: health_wellness
  -> user_intent: advice_guidance

- "Should I choose treatment A or treatment B?"
  -> primary_topic: health_wellness
  -> user_intent: decision_support

- "Why does my Python code throw this error?"
  -> primary_topic: coding_tech
  -> user_intent: problem_solving

- "Write a Python function that does X."
  -> primary_topic: coding_tech
  -> user_intent: creation_generation

- "Rewrite this Python function to be faster."
  -> primary_topic: coding_tech
  -> user_intent: editing_rewriting

- "Analyze this spreadsheet and identify the trends."
  -> primary_topic: document_analysis
  -> user_intent: analysis_extraction

- "Plan a 7-day trip to Spain."
  -> primary_topic: travel_recommendations
  -> user_intent: planning_recommendations

- "Explain how recursion works."
  -> primary_topic: coding_tech
  -> user_intent: learning_explanation

- "I'm stressed about my situation at work."
  -> primary_topic: mental_wellbeing
  -> user_intent: emotional_support

When multiple intents appear, choose the user's PRIMARY intent based on the
main goal of the conversation.

TASK OUTCOME:

Choose exactly one value from:

{", ".join(TASK_OUTCOMES)}

- completed: The user's goal was achieved.
- partially_completed: Meaningful progress was made, but the goal was not
  fully achieved.
- failed: The conversation did not accomplish the user's goal.
- unclear: There is insufficient evidence to determine whether the goal was
  achieved.
- not_applicable: There is no meaningful task outcome to evaluate.

ABANDONMENT:

Set true only when the user appears to have stopped pursuing an unresolved
goal. Do not infer abandonment merely because the conversation ends.

FOLLOW-UP:

Set true only when additional information, action, or interaction is needed
to achieve the user's goal.
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

For primary_topic, choose exactly one of the allowed taxonomy values.

For user_intent, choose exactly one of the allowed intent values.

Use the topic and intent definitions in the system instructions as
classification guidance.

Remember:
- primary_topic = WHAT the conversation is about
- user_intent = WHAT THE USER IS TRYING TO ACCOMPLISH

Return only the taxonomy values for these fields.

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
- For primary_topic, use exactly one allowed topic taxonomy value.
- For user_intent, use exactly one allowed user intent taxonomy value.
- Do not create new topic or intent categories.

Remember:

primary_topic = WHAT the conversation is about.

user_intent = WHAT THE USER IS TRYING TO ACCOMPLISH.

SESSIONS:
{sessions_text}
"""