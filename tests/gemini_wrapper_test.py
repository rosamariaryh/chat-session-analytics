from llm_wrappers.gemini_client import GeminiClient
from dotenv import load_dotenv

load_dotenv()

def test_gemini_connection():
    print("Creating Gemini client...")
    client = GeminiClient()

    print("Sending test request to Gemini...")
    response = client.generate(
        "Reply with exactly: Gemini connection works."
    )

    print(f"Gemini response: {response}")

    assert response.strip() == "Gemini connection works."

    print("✓ Gemini API connection is working!")


if __name__ == "__main__":
    test_gemini_connection()