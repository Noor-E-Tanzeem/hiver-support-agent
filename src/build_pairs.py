import pandas as pd
from pathlib import Path

RAW_FILE = "data/raw/twcs/twcs.csv"
OUTPUT_FILE = "data/processed/apple_pairs.csv"

print("Loading dataset...")

df = pd.read_csv(
    RAW_FILE,
    dtype={
        "tweet_id": "string",
        "author_id": "string",
        "inbound": "boolean",
        "text": "string",
        "response_tweet_id": "string",
        "in_response_to_tweet_id": "string",
    },
)

print(f"Rows loaded: {len(df)}")

# Build a lookup using tweet_id as the key.
# The tweet_id itself is kept separately as the dictionary key.
tweet_lookup = (
    df[["tweet_id", "author_id", "text"]]
    .set_index("tweet_id")
    .to_dict("index")
)

# Customer tweets that have at least one response.
customer_tweets = df[
    (df["inbound"] == True)
    & df["response_tweet_id"].notna()
].copy()

print(f"Customer tweets with responses: {len(customer_tweets)}")

pairs = []

for _, row in customer_tweets.iterrows():

    response_ids = str(row["response_tweet_id"]).split(",")

    for response_id in response_ids:

        response_id = response_id.strip()

        if response_id not in tweet_lookup:
            continue

        reply = tweet_lookup[response_id]

        # Keep only replies written by AppleSupport.
        if reply["author_id"] != "AppleSupport":
            continue

        pairs.append(
            {
                "customer_tweet_id": row["tweet_id"],
                "customer_text": row["text"],
                "apple_reply_id": response_id,
                "apple_reply": reply["text"],
            }
        )

pairs_df = pd.DataFrame(pairs)

# Remove rows where either side is missing.
pairs_df = pairs_df.dropna(
    subset=["customer_text", "apple_reply"]
).reset_index(drop=True)

# Make sure output directory exists.
Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)

# Save processed pairs.
pairs_df.to_csv(OUTPUT_FILE, index=False)

print(f"AppleSupport pairs: {len(pairs_df)}")
print(f"Saved to: {OUTPUT_FILE}")

print("\nFirst 5 pairs:")
print(pairs_df.head(5).to_string(index=False))
