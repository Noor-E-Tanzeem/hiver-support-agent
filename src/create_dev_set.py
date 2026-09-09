import pandas as pd
from pathlib import Path

INPUT_FILE = "data/processed/apple_pairs.csv"
OUTPUT_FILE = "data/processed/development.csv"

DEV_SIZE = 5000
RANDOM_SEED = 42

print("Loading AppleSupport pairs...")

df = pd.read_csv(INPUT_FILE)

print(f"Source rows: {len(df)}")

# Randomly sample a development set.
# The fixed seed makes the result reproducible.
dev_df = df.sample(
    n=DEV_SIZE,
    random_state=RANDOM_SEED
).reset_index(drop=True)

# Save the development set.
Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)

dev_df.to_csv(OUTPUT_FILE, index=False)

print(f"Development rows: {len(dev_df)}")
print(f"Saved to: {OUTPUT_FILE}")

print("\nColumns:")
print(list(dev_df.columns))

print("\nFirst 5 examples:")
print(dev_df.head(5).to_string(index=False))
