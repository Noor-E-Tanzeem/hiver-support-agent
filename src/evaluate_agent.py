from pathlib import Path
import json

import pandas as pd

from agent import run_agent


ROOT = Path(__file__).resolve().parent.parent
GOLDEN_PATH = ROOT / "data" / "processed" / "golden_set_final.xlsx"
OUTPUT_PATH = ROOT / "data" / "processed" / "agent_predictions.csv"


def normalize_escalation(value):
    if isinstance(value, bool):
        return "yes" if value else "no"

    value = str(value).strip().lower()

    if value in {"yes", "true", "1"}:
        return "yes"

    if value in {"no", "false", "0"}:
        return "no"

    raise ValueError(f"Invalid escalation value: {value}")


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
    gold = pd.read_excel(GOLDEN_PATH)
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

    remaining = gold[
        ~gold["customer_tweet_id"].astype(str).isin(completed_ids)
    ]

    print(f"Golden examples: {len(gold)}")
    print(f"Already evaluated: {len(completed_ids)}")
    print(f"Remaining: {len(remaining)}")

    for _, row in remaining.iterrows():
        print(
            f"Evaluating {len(predictions) + 1}/{len(gold)} "
            f"(tweet_id={row['customer_tweet_id']})"
        )

        result = run_agent(row["customer_text"])

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
            "classifier_confidence": result["classifier_confidence"],

            "reply": result["reply"],

            "grounding_evidence": json.dumps(
                result["grounding_evidence"],
                ensure_ascii=False,
            ),

            "retrieved_cases": json.dumps(
                result["retrieved_cases"],
                ensure_ascii=False,
            ),
        })

        # Save after every successful example so the run can resume.
        pd.DataFrame(predictions).to_csv(
            OUTPUT_PATH,
            index=False,
        )

    results = pd.DataFrame(predictions)

    expected_ids = set(
        gold["customer_tweet_id"].astype(str)
    )

    actual_ids = set(
        results["customer_tweet_id"].astype(str)
    )

    missing_ids = expected_ids - actual_ids

    if missing_ids:
        raise RuntimeError(
            f"Agent evaluation incomplete: {len(missing_ids)} "
            "golden examples are missing predictions."
        )

    print("\n=== AGENT EVALUATION COMPLETE ===")
    print(f"Examples evaluated: {len(results)}")
    print(f"Saved predictions to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
