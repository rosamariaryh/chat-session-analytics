## Deterministic metrics

The following metrics are calculated directly from the input data without using an LLM:

- Interaction complexity
- Assistant message count
- User message count
- Platform count
- User tier count
- Attachment type count

These metrics are deterministic, meaning that the same input data produces the same metric values.

This also provides a measurable baseline alongside the LLM-generated classifications.

## LLM classification

The following attributes are extracted:

- **Language**
- **Primary topic** (class)
- **User intent** (class)
- **User goal** (free text)
- **Task outcome** — determines whether and how the user's task was resolved, providing an indicator of conversation effectiveness.
- **Abandonment** — identifies whether the user appears to have abandoned the interaction before 
- **Follow-up** — identifies whether the conversation indicates a need for further action or assistance.

The LLM is used for qualitative attributes that are difficult to derive reliably from deterministic rules alone.

Please see prompts/prompts_updated.py for the full definitions.

## Usage

The main focus is on understanding the user and whether they are satisfied with the conversation. This can be derived combining metrics like outcome, abandonment, and follow-up.
It is equally important to understand _what_ the user is trying to resolve - this can be derived from the primary topic, user intent, and user goal.

Combining deterministic and LLM-generated metrics provides a comprehensive understanding of the conversation, enabling more accurate analysis and decision-making.
For example, we can see whether android users tend to abandon the conversation more, or whether iOS users tend to use the chatbot for editing purposes.
This type of information is valuable for product development and marketing.