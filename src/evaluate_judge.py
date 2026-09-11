import argparse
import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, cohen_kappa_score

try:
    from .llm_client import generate
except ImportError:
    from llm_client import generate


ROOT = Path(__file__).resolve().parent.parent

INPUT_PATH = ROOT / "data" / "processed" / "generation_judge_inputs.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "judge_predictions.csv"


JUDGE_SYSTEM_PROMPT = """
You are evaluating an AI customer-support reply for an AppleSupport-style
support agent.

Judge the reply independently. Do NOT assume that the human escalation label
is correct, and do NOT use it as an input to your decision.

Evaluate the reply against:
1. The customer's message.
2. The predicted intent.
3. The historical evidence retrieved by the system.
4. The actual reply produced by the system.

Important evaluation rules:

- Helpfulness: Does the reply appropriately address the customer's need?
- Correctness and safety: Does it avoid unsupported claims, invented policies,
  invented diagnoses, guarantees, refunds, or unsafe troubleshooting?
- Historical grounding: If historical evidence exists, is the reply consistent
  with that evidence? Do not require verbatim copying.
- Escalation fit: Based only on the customer message and support context,
  should this case be escalated to human/private support?
- Overall quality: Overall quality of the generated response.

When historical evidence is weak or absent, a cautious request for more
information or appropriate routing is preferable to inventing detailed
troubleshooting.

Return ONLY valid JSON with exactly these fields:

{
  "helpfulness": 1,
  "correctness_safety": 1,
  "historical_grounding": 1,
  "escalation_fit": 1,
  "overall_quality": 1,
  "judge_should_escalate": true,
  "reason": "brief explanation"
}

All scores must be integers from 1 to 5.

For judge_should_escalate:
- true = the case should be routed/escalated to human/private support
- false = the case can reasonably be handled without escalation

Keep the reason concise and evidence-based.
"""


def parse_json(content):
    if not content:
        raise ValueError("Judge returned empty content.")

    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")

        if start == -1 or end == -1 or end <= start:
            raise

        result = json.loads(content[start:end + 1])

    if not isinstance(result, dict):
        raise ValueError("Judge response is not a JSON object.")

    required = {
        "helpfulness",
        "correctness_safety",
        "historical_grounding",
        "escalation_fit",
        "overall_quality",
        "judge_should_escalate",
        "reason",
    }

    missing = required - set(result)

    if missing:
        raise ValueError(
            f"Judge response missing fields: {sorted(missing)}"
        )

    score_fields = [
        "helpfulness",
        "correctness_safety",
        "historical_grounding",
        "escalation_fit",
        "overall_quality",
    ]

    for field in score_fields:
        value = result[field]

        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"{field} must be an integer from 1 to 5."
            )

        if not 1 <= value <= 5:
            raise ValueError(
                f"{field} must be between 1 and 5."
            )

    if not isinstance(result["judge_should_escalate"], bool):
        raise ValueError(
            "judge_should_escalate must be boolean."
        )

    if not isinstance(result["reason"], str):
        raise ValueError("reason must be a string.")

    return result


def build_user_prompt(row):
    evidence = row["retrieved_cases"]

    if pd.isna(evidence) or not str(evidence).strip():
        evidence = "[]"

    return f"""
CUSTOMER MESSAGE:
{row["customer_text"]}

SYSTEM PREDICTED INTENT:
{row["predicted_intent"]}

SYSTEM PREDICTED ESCALATION:
{row["predicted_escalate"]}

RETRIEVED HISTORICAL CASES:
{evidence}

GENERATED REPLY:
{row["reply"]}

Evaluate this response independently using the rubric.
"""


def select_sample(df, sample_size):
    """
    Deterministically select a balanced subset across:
    - human escalation label
    - retrieval availability
    - intent where possible

    The human escalation label is used ONLY for sampling, not shown to
    the judge and not used in the judge's decision.
    """

    if sample_size >= len(df):
        return df.copy()

    working = df.copy()

    working["human_escalate"] = (
        working["true_escalate"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("yes")
    )

    working["retrieval_group"] = (
        working["has_retrieval"]
        .astype(bool)
    )

    selected = []

    # First create four broad strata.
    groups = [
        (False, False),
        (False, True),
        (True, False),
        (True, True),
    ]

    per_group = sample_size // len(groups)
    remainder = sample_size % len(groups)

    for group_index, (escalate, has_retrieval) in enumerate(groups):
        group = working[
            (working["human_escalate"] == escalate)
            & (working["retrieval_group"] == has_retrieval)
        ].copy()

        n = per_group + (1 if group_index < remainder else 0)

        if len(group) > 0:
            selected.append(
                group.sample(
                    n=min(n, len(group)),
                    random_state=42 + group_index,
                )
            )

    result = pd.concat(selected, ignore_index=True)

    # If a sparse stratum prevented reaching the requested size,
    # fill deterministically from the remaining examples.
    if len(result) < sample_size:
        selected_ids = set(result["customer_tweet_id"].astype(str))

        remaining = working[
            ~working["customer_tweet_id"].astype(str).isin(selected_ids)
        ]

        fill = remaining.sample(
            n=min(sample_size - len(result), len(remaining)),
            random_state=123,
        )

        result = pd.concat([result, fill], ignore_index=True)

    return result.head(sample_size)


def evaluate_example(row):
    messages = [
        {
            "role": "system",
            "content": JUDGE_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": build_user_prompt(row),
        },
    ]

    content = generate(
        messages,
        json_mode=True,
        max_tokens=800,
    )

    try:
        return parse_json(content)
    except Exception as primary_error:
        print(
            "Judge returned invalid output; retrying once with a stricter instruction."
        )

        retry_messages = [
            messages[0],
            {
                "role": "user",
                "content": messages[1]["content"] + "\n\nIMPORTANT: Your previous response was invalid. Return ONLY JSON. Every score must be an INTEGER from exactly 1, 2, 3, 4, or 5. Do not use 0, 6, decimals, strings, or other values.",
            },
        ]

        retry_content = generate(
            retry_messages,
            json_mode=True,
            max_tokens=800,
        )

        return parse_json(retry_content)


def print_metrics(df):
    print()
    print("=== LLM-AS-JUDGE RESULTS ===")
    print(f"Judged examples: {len(df)}")

    for field in [
        "helpfulness",
        "correctness_safety",
        "historical_grounding",
        "escalation_fit",
        "overall_quality",
    ]:
        print(
            f"Mean {field}: "
            f"{df[field].mean():.2f}"
        )

    human = (
        df["true_escalate"]
        .astype(str)
        .str.strip()
        .str.lower()
        .eq("yes")
    )

    judge = df["judge_should_escalate"].astype(bool)

    print()
    print("=== ESCALATION AGREEMENT ===")
    print(
        f"Accuracy/agreement: "
        f"{accuracy_score(human, judge):.3f}"
    )
    print(
        f"Cohen's kappa: "
        f"{cohen_kappa_score(human, judge):.3f}"
    )

    print()
    print("Confusion matrix:")
    print(
        pd.crosstab(
            human.rename("human"),
            judge.rename("judge"),
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description="LLM-as-judge evaluation for generated support replies."
    )

    parser.add_argument(
        "--sample",
        type=int,
        default=20,
        help="Number of clean generation examples to judge.",
    )

    args = parser.parse_args()

    df = pd.read_csv(INPUT_PATH)

    if df.empty:
        raise ValueError("Judge input file is empty.")

    if "has_retrieval" not in df.columns:
        df["has_retrieval"] = (
            df["retrieved_cases"]
            .fillna("[]")
            .astype(str)
            .str.strip()
            .ne("[]")
        )

    print(f"Available clean generation examples: {len(df)}")

    if OUTPUT_PATH.exists():
        existing = pd.read_csv(OUTPUT_PATH)

        completed_ids = set(
            existing["customer_tweet_id"].astype(str)
        )

        print(
            f"Found {len(existing)} existing judge results. "
            "Resuming."
        )
    else:
        existing = pd.DataFrame()
        completed_ids = set()

        print("No existing judge results found.")

    # Select the deterministic evaluation sample.
    sample = select_sample(df, min(args.sample, len(df)))

    # Never regenerate examples already judged.
    sample = sample[
        ~sample["customer_tweet_id"]
        .astype(str)
        .isin(completed_ids)
    ].copy()

    print(f"New examples to judge in this run: {len(sample)}")

    if sample.empty:
        print("Nothing new to judge.")
        if not existing.empty:
            print_metrics(existing)
        return

    results = []

    for index, (_, row) in enumerate(
        sample.iterrows(),
        start=1,
    ):
        print(
            f"Judging {index}/{len(sample)} "
            f"(tweet_id={row['customer_tweet_id']})"
        )

        try:
            judgment = evaluate_example(row)

            result = {
                "customer_tweet_id": row["customer_tweet_id"],
                "customer_text": row["customer_text"],
                "true_intent": row["true_intent"],
                "true_escalate": row["true_escalate"],
                "predicted_intent": row["predicted_intent"],
                "predicted_escalate": row["predicted_escalate"],
                "reply": row["reply"],
                "has_retrieval": row["has_retrieval"],
                **judgment,
            }

            results.append(result)

        except Exception as error:
            print(
                f"Judge failed for tweet_id="
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

    if OUTPUT_PATH.exists():
        final = pd.read_csv(OUTPUT_PATH)
        print_metrics(final)

    print()
    print(f"Saved results to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
