import pandas as pd
from pathlib import Path

INPUT_FILE = "data/processed/golden_candidates.csv"
OUTPUT_FILE = "data/processed/golden_set.csv"

print("Loading golden candidates...")

df = pd.read_csv(INPUT_FILE)

# Keep only the fields needed for human annotation.
annotation_df = df[
    [
        "customer_tweet_id",
        "customer_text",
        "apple_reply_id",
        "apple_reply",
    ]
].copy()

# Add blank fields for the human annotator.
annotation_df["intent"] = ""
annotation_df["should_escalate"] = ""
annotation_df["escalation_reason"] = ""
annotation_df["annotation_notes"] = ""

Path(OUTPUT_FILE).parent.mkdir(
    parents=True,
    exist_ok=True
)

annotation_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print(f"Annotation rows: {len(annotation_df)}")
print(f"Saved to: {OUTPUT_FILE}")

print("\nColumns:")
print(list(annotation_df.columns))

print("\nFirst 5 rows:")
print(annotation_df.head(5).to_string(index=False))
