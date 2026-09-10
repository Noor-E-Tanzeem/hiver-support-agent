from pathlib import Path
import argparse
import time

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    confusion_matrix,
)

try:
    from .classifier import classify
except ImportError:
    from classifier import classify


ROOT = Path(__file__).resolve().parent.parent
GOLDEN_PATH = ROOT / "data" / "processed" / "golden_set_final.xlsx"
OUTPUT_PATH = ROOT / "data" / "processed" / "classifier_predictions.csv"


def normalize_escalation(value):
    if isinstance(value, bool):
        return "yes" if value else "no"

    value = str(value).strip().lower()

    if value in {"yes", "true", "1"}:
        return "yes"

    if value in {"no", "false", "0"}:
        return "no"

    raise ValueError(f"Invalid escalation value: {value}")


def classify_with_retry(text, max_retries=3):
    empty_response_retried = False

    for attempt in range(max_retries):
        try:
            return classify(text)

        except Exception as e:
            message = str(e).lower()

            # A reasoning model can occasionally return empty visible
            # content. Retry this once rather than losing the run.
            if "classifier returned empty content" in message:
                if empty_response_retried:
                    raise RuntimeError(
                        "Classifier returned empty content after retry."
                    )

                empty_response_retried = True

                print(
                    "Classifier returned empty content. "
                    "Retrying once..."
                )

                time.sleep(1)
                continue

            # Groq JSON mode can occasionally fail to produce a valid
            # JSON document even when the same prompt succeeds on retry.
            if "json_validate_failed" in message:
                wait_seconds = 2

                print(
                    "Groq JSON generation failed. "
                    f"Retrying in {wait_seconds}s..."
                )

                time.sleep(wait_seconds)
                continue

            # Handle temporary rate limits.
            if "429" not in message and "rate_limit" not in message:
                raise

            # Do not repeatedly retry a daily quota exhaustion.
            if "tokens per day" in message or "tpd" in message:
                raise RuntimeError(
                    "Groq daily token quota is exhausted. "
                    "Resume the evaluation when the quota is available."
                )

            wait_seconds = min(10 * (attempt + 1), 60)

            print(
                f"Rate limited. Waiting {wait_seconds}s "
                f"before retry {attempt + 1}/{max_retries}..."
            )

            time.sleep(wait_seconds)

    raise RuntimeError("Maximum retries exceeded.")


def load_existing_predictions():
    if not OUTPUT_PATH.exists():
        return pd.DataFrame()

    existing = pd.read_csv(OUTPUT_PATH)

    if "customer_tweet_id" not in existing.columns:
        raise ValueError(
            "Existing predictions file is missing customer_tweet_id."
        )

    return existing


def print_results(results):
    print("\n=== INTENT RESULTS ===")

    intent_accuracy = accuracy_score(
        results["true_intent"],
        results["predicted_intent"],
    )

    intent_macro_f1 = f1_score(
        results["true_intent"],
        results["predicted_intent"],
        average="macro",
        zero_division=0,
    )

    print("Accuracy:", round(intent_accuracy, 3))
    print("Macro-F1:", round(intent_macro_f1, 3))

    print(
        classification_report(
            results["true_intent"],
            results["predicted_intent"],
            zero_division=0,
        )
    )

    print("\n=== ESCALATION RESULTS ===")

    escalation_accuracy = accuracy_score(
        results["true_escalate"],
        results["predicted_escalate"],
    )

    escalation_macro_f1 = f1_score(
        results["true_escalate"],
        results["predicted_escalate"],
        average="macro",
        zero_division=0,
    )

    escalation_recall = f1_score(
        results["true_escalate"],
        results["predicted_escalate"],
        average=None,
        labels=["yes"],
        zero_division=0,
    )[0]

    print("Accuracy:", round(escalation_accuracy, 3))
    print("Macro-F1:", round(escalation_macro_f1, 3))
    print("Escalation recall:", round(escalation_recall, 3))

    print(
        classification_report(
            results["true_escalate"],
            results["predicted_escalate"],
            zero_division=0,
        )
    )

    print("\n=== ESCALATION CONFUSION MATRIX ===")

    print(
        pd.DataFrame(
            confusion_matrix(
                results["true_escalate"],
                results["predicted_escalate"],
                labels=["no", "yes"],
            ),
            index=["true_no", "true_yes"],
            columns=["pred_no", "pred_yes"],
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate the classifier on the frozen golden set."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of NEW examples to evaluate in this run.",
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        raise ValueError("--limit must be a positive integer.")

    df = pd.read_excel(GOLDEN_PATH)
    existing = load_existing_predictions()

    if existing.empty:
        predictions = []
        completed_ids = set()
    else:
        predictions = existing.to_dict("records")
        completed_ids = set(
            existing["customer_tweet_id"].astype(str)
        )

        print(
            f"Found {len(existing)} existing predictions. "
            "Resuming from remaining examples."
        )

    remaining = df[
        ~df["customer_tweet_id"].astype(str).isin(completed_ids)
    ]

    if args.limit is not None:
        remaining = remaining.head(args.limit)

    print(f"Golden examples: {len(df)}")
    print(f"Already evaluated: {len(completed_ids)}")
    print(f"Remaining in this run: {len(remaining)}")

    for _, row in remaining.iterrows():
        current_count = len(predictions) + 1

        print(
            f"Evaluating {current_count}/{len(df)} "
            f"(tweet_id={row['customer_tweet_id']})"
        )

        result = classify_with_retry(row["customer_text"])

        predictions.append(
            {
                "customer_tweet_id": row["customer_tweet_id"],
                "customer_text": row["customer_text"],
                "true_intent": row["intent"],
                "predicted_intent": result["intent"],
                "true_escalate": normalize_escalation(
                    row["should_escalate"]
                ),
                "predicted_escalate": normalize_escalation(
                    result["should_escalate"]
                ),
                "predicted_reason": result["escalation_reason"],
                "confidence": result["confidence"],
            }
        )

        # Save after every successful prediction so the evaluation
        # can resume safely after interruption or quota exhaustion.
        pd.DataFrame(predictions).to_csv(
            OUTPUT_PATH,
            index=False,
        )

    results = pd.DataFrame(predictions)

    expected_ids = set(
        df["customer_tweet_id"].astype(str)
    )

    actual_ids = set(
        results["customer_tweet_id"].astype(str)
    )

    missing_ids = expected_ids - actual_ids

    if missing_ids:
        print(
            f"\nEvaluation batch complete. "
            f"{len(missing_ids)} golden examples still need predictions."
        )
        print(
            "Final metrics will be reported only after all 200 "
            "golden examples are evaluated."
        )
        return

    print_results(results)

    print(
        f"\nSaved predictions to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()
