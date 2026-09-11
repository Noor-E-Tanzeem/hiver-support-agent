import argparse
import json
from pathlib import Path

import pandas as pd

try:
    from .generator import generate_reply
    from .retrieval import HistoricalRetriever
    from .agent import build_evidence
except ImportError:
    from generator import generate_reply
    from retrieval import HistoricalRetriever
    from agent import build_evidence


ROOT = Path(__file__).resolve().parent.parent

GOLDEN_PATH = ROOT / "data" / "processed" / "golden_set_final.xlsx"
CLASSIFIER_PATH = ROOT / "data" / "processed" / "classifier_predictions.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "generation_predictions.csv"


retriever = HistoricalRetriever()


def load_classifier_predictions():
    classifier = pd.read_csv(CLASSIFIER_PATH)

    required_columns = {
        "customer_tweet_id",
        "predicted_intent",
        "predicted_escalate",
        "predicted_reason",
        "confidence",
    }

    missing = required_columns - set(classifier.columns)

    if missing:
        raise ValueError(
            f"classifier_predictions.csv is missing columns: {sorted(missing)}"
        )

    classifier["customer_tweet_id"] = (
        classifier["customer_tweet_id"].astype(str)
    )

    return classifier.set_index("customer_tweet_id")


def evaluate_example(row, classifier_predictions):
    tweet_id = str(row["customer_tweet_id"])

    if tweet_id not in classifier_predictions.index:
        raise ValueError(
            f"No saved classifier prediction for tweet_id={tweet_id}"
        )

    prediction = classifier_predictions.loc[tweet_id]

    predicted_intent = prediction["predicted_intent"]

    predicted_escalate = (
        str(prediction["predicted_escalate"]).strip().lower() == "true"
    )

    predicted_reason = prediction["predicted_reason"]

    if pd.isna(predicted_reason):
        predicted_reason = ""

    confidence = prediction["confidence"]

    if pd.isna(confidence):
        confidence = 0.0

    results = retriever.search(
        row["customer_text"],
        top_k=3,
        min_similarity=0.45,
    )

    evidence = build_evidence(results)

    generated = generate_reply(
        customer_message=row["customer_text"],
        intent=predicted_intent,
        should_escalate=predicted_escalate,
        escalation_reason=predicted_reason,
        historical_evidence=evidence,
    )

    return {
        "customer_tweet_id": row["customer_tweet_id"],
        "customer_text": row["customer_text"],
        "true_intent": row["intent"],
        "true_escalate": row["should_escalate"],
        "human_escalation_reason": row["escalation_reason"],
        "predicted_intent": predicted_intent,
        "predicted_escalate": predicted_escalate,
        "predicted_reason": predicted_reason,
        "classifier_confidence": confidence,
        "reply": generated["reply"],
        "grounding_evidence": json.dumps(
            generated["grounding_evidence"],
            ensure_ascii=False,
        ),
        "retrieved_cases": json.dumps(
            evidence,
            ensure_ascii=False,
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate response generation on the golden set."
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of new examples to evaluate.",
    )

    args = parser.parse_args()

    golden = pd.read_excel(GOLDEN_PATH)
    classifier_predictions = load_classifier_predictions()

    if OUTPUT_PATH.exists():
        existing = pd.read_csv(OUTPUT_PATH)

        completed_ids = set(
            existing["customer_tweet_id"].astype(str)
        )

        print(
            f"Found {len(existing)} existing generation results. "
            "Resuming from remaining examples."
        )
    else:
        existing = pd.DataFrame()
        completed_ids = set()

        print("No existing generation results found.")

    remaining = golden[
        ~golden["customer_tweet_id"].astype(str).isin(completed_ids)
    ].copy()

    if args.limit is not None:
        remaining = remaining.head(args.limit)

    print(f"Golden examples: {len(golden)}")
    print(f"Already generated: {len(existing)}")
    print(f"Remaining in this run: {len(remaining)}")
    print(
        "Using saved classifier predictions; "
        "no classifier API calls will be made."
    )

    if remaining.empty:
        print("Nothing new to evaluate.")
        return

    results = []

    for index, (_, row) in enumerate(
        remaining.iterrows(),
        start=1,
    ):
        completed_number = len(existing) + index

        print(
            f"Generating {completed_number}/{len(golden)} "
            f"(tweet_id={row['customer_tweet_id']})"
        )

        try:
            result = evaluate_example(
                row,
                classifier_predictions,
            )

            results.append(result)

        except Exception as error:
            print(
                f"Generation failed for tweet_id="
                f"{row['customer_tweet_id']}: {error}"
            )

            print(
                "Stopping so successful results remain checkpointed."
            )

            break

        checkpoint = pd.DataFrame(results)

        if not existing.empty:
            combined = pd.concat(
                [existing, checkpoint],
                ignore_index=True,
            )
        else:
            combined = checkpoint

        combined.to_csv(
            OUTPUT_PATH,
            index=False,
        )

    final_count = len(existing) + len(results)

    print()
    print("Generation batch complete.")
    print(
        f"{len(golden) - final_count} golden examples "
        "still need generation."
    )
    print(f"Saved results to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
