import pandas as pd
from pathlib import Path

SOURCE_FILE = "data/processed/apple_pairs.csv"
DEV_FILE = "data/processed/development.csv"
OUTPUT_FILE = "data/processed/golden_candidates.csv"

GOLDEN_SIZE = 200
COVERAGE_SIZE = 120
RANDOM_SIZE = 80
RANDOM_SEED = 42

print("Loading source pairs...")
df = pd.read_csv(SOURCE_FILE)

print(f"Source rows: {len(df)}")

print("Loading development set...")
dev_df = pd.read_csv(DEV_FILE)

# Exclude every customer message already used in development.
dev_customer_ids = set(
    dev_df["customer_tweet_id"].astype(str)
)

df["customer_tweet_id"] = df["customer_tweet_id"].astype(str)

before = len(df)

df = df[
    ~df["customer_tweet_id"].isin(dev_customer_ids)
].copy()

print(f"Excluded development customer messages: {before - len(df)}")
print(f"Eligible golden-set pool: {len(df)}")

text = df["customer_text"].fillna("").str.lower()

# These signals are ONLY used to improve coverage.
# They do NOT assign the final human intent labels.

sampling_groups = {
    "battery_charging": text.str.contains(
        r"\bbattery\b|\bcharging\b|\bcharger\b|\bcharge\b",
        regex=True,
        na=False,
    ),

    "software_update": text.str.contains(
        r"\bios\s*\d|\bios11\b|\bupdate\b|\bupgrade\b",
        regex=True,
        na=False,
    ),

    "connectivity_communication": text.str.contains(
        r"\bwifi\b|\bwi-fi\b|\bbluetooth\b|\bimessage\b|"
        r"\bmessages?\b|\bcalls?\b|\bcalling\b|\bcellular\b|"
        r"\bmobile data\b",
        regex=True,
        na=False,
    ),

    "apps_services": text.str.contains(
        r"\bapple music\b|\bicloud\b|\bphotos?\b|\bsiri\b|"
        r"\bsafari\b|\bapp store\b|\bitunes\b",
        regex=True,
        na=False,
    ),

    "orders_account_billing": text.str.contains(
        r"\baccount\b|\bhacked\b|\bphishing\b|\bbilling\b|"
        r"\brefund\b|\breimburse\b|\border\b|\breservation\b|"
        r"\bpurchase\b|\bsubscription\b|\bpayment\b",
        regex=True,
        na=False,
    ),

    "hardware_accessories": text.str.contains(
        r"\bairpods?\b|\bscreen\b|\bdisplay\b|\bbroken\b|"
        r"\bdamaged\b|\bcable\b|\badapter\b|\bheadphones?\b",
        regex=True,
        na=False,
    ),

    "settings_how_to": text.str.contains(
        r"\bhow do i\b|\bhow can i\b|\bwhere is\b|\bhow to\b|"
        r"\bturn off\b|\bturn on\b|\benable\b|\bdisable\b|\bsetting\b",
        regex=True,
        na=False,
    ),

    "device_malfunction": text.str.contains(
        r"\bfreez(?:e|es|ing)\b|\brestart(?:s|ed|ing)?\b|"
        r"\bcrash(?:es|ed|ing)?\b|\bslow\b|\bsluggish\b|"
        r"\bwon't work\b|\bnot working\b",
        regex=True,
        na=False,
    ),
}

# ---------------------------------------------------------------
# Part 1: coverage sample
# ---------------------------------------------------------------

coverage_indices = []

PER_GROUP = 15

for group_name, mask in sampling_groups.items():

    candidates = df[mask]

    if len(candidates) == 0:
        print(f"{group_name}: no candidates")
        continue

    n = min(PER_GROUP, len(candidates))

    sampled = candidates.sample(
        n=n,
        random_state=RANDOM_SEED
    )

    coverage_indices.extend(
        sampled.index.tolist()
    )

    print(
        f"{group_name}: {len(candidates)} candidates -> "
        f"{n} sampled"
    )

# Remove duplicates caused by overlapping groups.
coverage_indices = list(
    dict.fromkeys(coverage_indices)
)

# Keep coverage portion at 120.
if len(coverage_indices) > COVERAGE_SIZE:
    coverage_indices = (
        pd.Series(coverage_indices)
        .sample(
            n=COVERAGE_SIZE,
            random_state=RANDOM_SEED
        )
        .tolist()
    )

coverage_df = df.loc[
    coverage_indices
].copy()

# ---------------------------------------------------------------
# Part 2: random sample
# ---------------------------------------------------------------

remaining_df = df.drop(
    index=coverage_indices
)

random_df = remaining_df.sample(
    n=RANDOM_SIZE,
    random_state=RANDOM_SEED
)

# Combine coverage + random examples.
golden_df = pd.concat(
    [coverage_df, random_df],
    ignore_index=True
)

# Safety checks.
if len(golden_df) != GOLDEN_SIZE:
    raise ValueError(
        f"Expected {GOLDEN_SIZE} rows, "
        f"got {len(golden_df)}"
    )

if golden_df["customer_tweet_id"].duplicated().any():
    raise ValueError(
        "Duplicate customer messages found "
        "in golden set."
    )

# Shuffle final ordering.
golden_df = golden_df.sample(
    frac=1,
    random_state=RANDOM_SEED
).reset_index(drop=True)

# Add blank human annotation fields.
golden_df["intent"] = ""
golden_df["should_escalate"] = ""
golden_df["escalation_reason"] = ""
golden_df["annotation_notes"] = ""

Path(OUTPUT_FILE).parent.mkdir(
    parents=True,
    exist_ok=True
)

golden_df.to_csv(
    OUTPUT_FILE,
    index=False
)

print()
print(f"Coverage examples: {len(coverage_df)}")
print(f"Random examples: {len(random_df)}")
print(f"Golden candidates: {len(golden_df)}")
print(f"Saved to: {OUTPUT_FILE}")

print()
print("Columns:")
print(list(golden_df.columns))

print()
print("First 5 candidates:")
print(
    golden_df[
        [
            "customer_tweet_id",
            "customer_text",
            "apple_reply",
            "intent",
            "should_escalate",
            "escalation_reason",
            "annotation_notes",
        ]
    ]
    .head(5)
    .to_string(index=False)
)
