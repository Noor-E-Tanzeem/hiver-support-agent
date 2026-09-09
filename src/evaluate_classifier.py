from pathlib import Path
import time

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report

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
    for attempt in range(max_retries):
        try:
            return classify(text)

        except Exception as e:
            message = str(e).lower()

            if "429" not in message and "rate_limit" not in message:
                raise

            # Do not repeatedly retry a daily token-quota exhaustion.
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


def main():
    df = pd.read_excel(GOLDEN_PATH)
    existing = load_existing_predictions()

    if existing.empty:
        predictions = []
        completed_ids = set()
    else:
        predictions = existing.to_dict("records")
        completed_ids = set(existing["customer_tweet_id"].astype(str))

        print(
            f"Found {len(existing)} existing predictions. "
            "Resuming from the remaining examples."
        )

    remaining = df[
        ~df["customer_tweet_id"].astype(str).isin(completed_ids)
    ]

    print(f"Golden examples: {len(df)}")
    print(f"Already evaluated: {len(completed_ids)}")
    print(f"Remaining: {len(remaining)}")

    for _, row in remaining.iterrows():
        current_count = len(predictions) + 1

        print(
            f"Evaluating {current_count}/{len(df)} "
            f"(tweet_id={row['customer_tweet_id']})"
        )

        result = classify_with_retry(row["customer_text"])

        predictions.append({
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
        })

        # Save after every successful prediction.
        pd.DataFrame(predictions).to_csv(
            OUTPUT_PATH,
            index=False,
        )

    results = pd.DataFrame(predictions)

    print("\n=== INTENT RESULTS ===")
    print(
        "Accuracy:",
        round(
            accuracy_score(
                results["true_intent"],
                results["predicted_intent"],
            ),
            3,
        ),
    )

    print(
        classification_report(
            results["true_intent"],
            results["predicted_intent"],
            zero_division=0,
        )
    )

    print("\n=== ESCALATION RESULTS ===")
    print(
        "Accuracy:",
        round(
            accuracy_score(
                results["true_escalate"],
                results["predicted_escalate"],
            ),
            3,
        ),
    )

    print(
        classification_report(
            results["true_escalate"],
            results["predicted_escalate"],
            zero_division=0,
        )
    )

    print(f"\nSaved predictions to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
