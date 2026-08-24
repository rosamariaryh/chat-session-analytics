from llm_wrappers.client import get_llm_client
from llm_wrappers.client import get_batch_schema

from prompts.prompts_1 import SYSTEM_INSTRUCTIONS


def main():
    client = get_llm_client()
    schema = get_batch_schema()

    print(f"Provider: {type(client).__name__}")
    print(f"Model: {client.model}")

    result = client.generate_structured(
        prompt="""
Analyze this session:

USER: How do I reset my password?
ASSISTANT: Go to Settings and select Reset Password.

Return the required classification.
""",
        system_instruction=SYSTEM_INSTRUCTIONS,
        schema=schema,
    )

    print("Result:")
    print(result)


if __name__ == "__main__":
    main()