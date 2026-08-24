# batching.py
from .config import BATCH_SIZE

def create_batches(
    sessions: list[dict],
    completed: dict[int, dict],
) -> list[list[tuple[int, dict]]]:
    """
    Create batches of unprocessed sessions.

    Each item is:
        (original_session_index, session)
    """

    remaining = [
        (index, session)
        for index, session in enumerate(sessions)
        if index not in completed
    ]

    return [
        remaining[i:i + BATCH_SIZE]
        for i in range(
            0,
            len(remaining),
            BATCH_SIZE,
        )
    ]