import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


GOLDEN_PATH = "data/processed/golden_set_final.xlsx"


def main():
    df = pd.read_excel(GOLDEN_PATH)

    # Trivial intent baseline:
    # Always predict the majority intent from the golden set.
    majority_intent = df["intent"].value_counts().idxmax()
    intent_predictions = [majority_intent] * len(df)

    print("=== INTENT BASELINE ===")
    print("Majority intent:", majority_intent)
    print(
        "Accuracy:",
        round(accuracy_score(df["intent"], intent_predictions), 3),
    )
    print(
        classification_report(
            df["intent"],
            intent_predictions,
            zero_division=0,
        )
    )

    # Trivial escalation baseline:
    # Always predict the majority escalation decision.
    majority_escalation = df["should_escalate"].value_counts().idxmax()
    escalation_predictions = [majority_escalation] * len(df)

    print("=== ESCALATION BASELINE ===")
    print("Majority decision:", majority_escalation)
    print(
        "Accuracy:",
        round(
            accuracy_score(
                df["should_escalate"],
                escalation_predictions,
            ),
            3,
        ),
    )
    print(
        classification_report(
            df["should_escalate"],
            escalation_predictions,
            zero_division=0,
        )
    )


if __name__ == "__main__":
    main()
