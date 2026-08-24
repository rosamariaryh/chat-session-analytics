"""
Validate, preprocess, and classify chatbot sessions using OpenRouter or Gemini.

The pipeline is:

raw data
    -> validation
    -> preprocessing
    -> LLM classification
    -> merge
    -> classified JSONL and CSV + run-level summary

Usage:
    uv run python main.py data/raw/<file>.jsonl
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from app.batching import create_batches
from app.classify import classify_batch, client
from app.config import (
    BATCH_SIZE,
    REQUESTS_PER_MINUTE,
    MAX_RETRIES,
    MAX_CONCURRENCY,
    PROVIDER,
)
from app.io_utils import (
    append_results,
    append_session_csv,
    load_completed_sessions,
    save_classification_summary,
    remove_internal_classification_fields,
)
from app.load_data import load_and_validate
from app.preprocess import process_session

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    start_time = time.perf_counter()

    parser = argparse.ArgumentParser()
    parser.add_argument("input_path")

    args = parser.parse_args()

    input_path = Path(args.input_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    # -----------------------------------------------------------------------
    # Output paths
    # -----------------------------------------------------------------------

    output_dir = (
        input_path.parents[1] / "classified"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    sessions_jsonl_path = (
            output_dir
            / f"{timestamp}_{input_path.stem}_sessions.jsonl"
    )

    sessions_csv_path = (
            output_dir
            / f"{timestamp}_{input_path.stem}_sessions.csv"
    )

    summary_json_path = (
            output_dir
            / f"{timestamp}_{input_path.stem}_summary.json"
    )

    # -----------------------------------------------------------------------
    # Validate and preprocess sessions in memory
    # -----------------------------------------------------------------------

    sessions = load_and_validate(
        input_path
    )

    sessions = [
        process_session(session)
        for session in sessions
    ]

    total = len(sessions)

    completed = load_completed_sessions(
        sessions_jsonl_path
    )


    # -----------------------------------------------------------------------
    # Create batches
    # -----------------------------------------------------------------------

    batches = create_batches(
        sessions,
        completed,
    )

    total_batches = len(batches)

    # -----------------------------------------------------------------------
    # Status
    # -----------------------------------------------------------------------

    print(
        f"Loaded {total} sessions."
    )

    print(
        f"LLM provider: {PROVIDER}"
    )

    print(
        f"Model: {client.model}"
    )

    print(
        f"Already classified: "
        f"{len(completed)}"
    )

    print(
        f"Remaining sessions: "
        f"{total - len(completed)}"
    )

    print(
        f"Batch size: "
        f"{BATCH_SIZE} sessions/request"
    )

    print(
        f"Requests remaining this run: "
        f"{total_batches}"
    )

    print(
        f"Using {MAX_CONCURRENCY} concurrent workers."
    )

    print(
        f"Configured rate limit: "
        f"{REQUESTS_PER_MINUTE} requests/minute."
    )

    print(
        f"Max retries per batch: "
        f"{MAX_RETRIES}"
    )

    print()

    # -----------------------------------------------------------------------
    # Nothing to process
    # -----------------------------------------------------------------------

    if not batches:

        # Even if there is nothing new to classify, rebuild the summary
        # from all completed sessions. This keeps the summary correct
        # when rerunning an already-completed dataset.

        save_classification_summary(
            summary_json_path,
            completed,
        )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print(
            "Nothing to process."
        )

        print(
            f"Sessions JSONL: "
            f"{sessions_jsonl_path}"
        )

        print(
            f"Sessions CSV:   "
            f"{sessions_csv_path}"
        )

        print(
            f"Summary JSON:   "
            f"{summary_json_path}"
        )
        print(
            f"Processing time: "
            f"{elapsed:.2f} seconds"
        )

        return

    # -----------------------------------------------------------------------
    # Classification
    # -----------------------------------------------------------------------

    completed_count = len(completed)
    failed_batches = 0

    with ThreadPoolExecutor(
        max_workers=MAX_CONCURRENCY
    ) as executor:

        futures = {
            executor.submit(
                classify_batch,
                batch_index,
                batch,
            ): batch_index
            for batch_index, batch in enumerate(
                batches
            )
        }

        for future in as_completed(
            futures
        ):

            batch_index = futures[
                future
            ]

            try:

                _, results = future.result()

                # -----------------------------------------------------------
                # Preserve the original preprocessed session fields.
                #
                # classify_batch() modifies the original session in place,
                # so the classification is already present. We still merge
                # explicitly to make preservation clear and robust.
                # -----------------------------------------------------------

                preserved_results = []

                for (
                    index,
                    classified_session,
                ) in results:

                    original_session = sessions[
                        index
                    ]

                    merged_session = {
                        **original_session,
                        **classified_session,
                    }

                    merged_session = remove_internal_classification_fields(
                        merged_session
                    )

                    preserved_results.append(
                        (
                            index,
                            merged_session,
                        )
                    )

                # -----------------------------------------------------------
                # Write completed sessions immediately.
                # -----------------------------------------------------------

                append_results(
                    sessions_jsonl_path,
                    preserved_results,
                )

                append_session_csv(
                    sessions_csv_path,
                    preserved_results,
                )

                # -----------------------------------------------------------
                # Update in-memory completed sessions.
                #
                # This is important because the summary is rebuilt from
                # ALL completed sessions, including sessions completed in
                # this run.
                # -----------------------------------------------------------

                for (
                    index,
                    session,
                ) in preserved_results:

                    completed[
                        index
                    ] = session

                completed_count += len(
                    preserved_results
                )

                # -----------------------------------------------------------
                # Rebuild the summary after every successful batch.
                #
                # This means the summary itself is also effectively
                # checkpointed.
                # -----------------------------------------------------------

                save_classification_summary(
                    summary_json_path,
                    completed,
                )

                print(
                    f"Completed batch "
                    f"{batch_index + 1}/"
                    f"{total_batches} "
                    f"({len(preserved_results)} "
                    f"sessions) "
                    f"— total "
                    f"{completed_count}/"
                    f"{total}"
                )

            except Exception as exc:

                failed_batches += 1

                batch = batches[
                    batch_index
                ]

                print(
                    f"FAILED batch "
                    f"{batch_index + 1}/"
                    f"{total_batches} "
                    f"(sessions "
                    f"{batch[0][0] + 1}-"
                    f"{batch[-1][0] + 1}): "
                    f"{exc}"
                )

    # -----------------------------------------------------------------------
    # Final summary
    # -----------------------------------------------------------------------

    save_classification_summary(
        summary_json_path,
        completed,
    )

    # -----------------------------------------------------------------------
    # Finished
    # -----------------------------------------------------------------------

    elapsed = (
        time.perf_counter()
        - start_time
    )

    print()

    print(
        f"Classified: "
        f"{completed_count}/"
        f"{total} sessions"
    )

    print(
        f"Failed batches: "
        f"{failed_batches}"
    )

    print(
        f"Sessions JSONL: "
        f"{sessions_jsonl_path}"
    )

    print(
        f"Sessions CSV:   "
        f"{sessions_csv_path}"
    )

    print(
        f"Summary JSON:   "
        f"{summary_json_path}"
    )

    print(
        f"Processing time: "
        f"{elapsed:.2f} seconds"
    )


if __name__ == "__main__":
    main()