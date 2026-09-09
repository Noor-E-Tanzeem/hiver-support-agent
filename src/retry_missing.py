from pathlib import Path
import time

import pandas as pd

from classifier import classify


ROOT = Path(__file__).resolve().parent.parent
GOLDEN_PATH = ROOT / "data" / "processed" / "golden_set_final.xlsx"
PREDICTIONS_PATH = ROOT / "data" / "processed" / "classifier_predictions.csv"


def normalize(value):
    if isinstance(value, bool):
        return "yes" if value else "no"

    value = str(value).strip().lower()

    if value in {"yes", "true", "1"}:
        return "yes"

    if value in {"no", "false", "0"}:
        return "no"

    raise ValueError(f"Invalid escalation value: {value}")


def main():
    golden = pd.read_excel(GOLDEN_PATH)
    predictions = pd.read_csv(PREDICTIONS_PATH)

    existing_ids = set(predictions["customer_tweet_id"].astype(str))

    missing = golden[
        ~golden["customer_tweet_id"].astype(str).isin(existing_ids)
    ]

    print(f"Missing examples: {len(missing)}")

    new_predictions = []

    for _, row in missing.iterrows():
        print(f"\nEvaluating: {row['customer_tweet_id']}")
        print(row["customer_text"])

        while True:
            try:
                result = classify(row["customer_text"])
                break
            except Exception as e:
                if "429" in str(e) or "rate_limit" in str(e):
                    print("Rate limited. Waiting 30 seconds...")
                    time.sleep(30)
                else:
                    raise

        new_predictions.append({
            "customer_tweet_id": row["customer_tweet_id"],
            "customer_text": row["customer_text"],
            "true_intent": row["intent"],
            "predicted_intent": result["intent"],
            "true_escalate": normalize(row["should_escalate"]),
            "predicted_escalate": normalize(result["should_escalate"]),
            "predicted_reason": result["escalation_reason"],
            "confidence": result["confidence"],
        })

        # Wait between requests so we don't immediately hit TPM again.
        time.sleep(10)

    if new_predictions:
        updated = pd.concat(
            [predictions, pd.DataFrame(new_predictions)],
            ignore_index=True,
        )

        updated.to_csv(PREDICTIONS_PATH, index=False)

        print(f"\nSaved {len(new_predictions)} new predictions.")
        print(f"Total predictions now: {len(updated)}")


if __name__ == "__main__":
    main()
