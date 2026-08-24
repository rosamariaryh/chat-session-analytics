# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

MAX_CONCURRENCY = int(os.getenv("LLM_MAX_CONCURRENCY", "5"))
MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
BATCH_SIZE = int(os.getenv("LLM_BATCH_SIZE", "10"))
REQUESTS_PER_MINUTE = int(os.getenv("LLM_REQUESTS_PER_MINUTE", "12"))