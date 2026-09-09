import pandas as pd

PATH = "data/raw/twcs/twcs.csv"
BRAND = "AppleSupport"

print("Loading dataset...")

df = pd.read_csv(
    PATH,
    usecols=[
        "tweet_id",
        "author_id",
        "inbound",
        "created_at",
        "text",
        "response_tweet_id",
        "in_response_to_tweet_id",
    ]
)

# Create tweet_id -> row lookup
tweets = df.set_index("tweet_id")

# AppleSupport's outgoing replies
apple_replies = df[
    (df["author_id"] == BRAND) &
    (df["in_response_to_tweet_id"].notna())
].copy()

# Customer tweets directly answered by AppleSupport
pairs = []

for _, reply in apple_replies.iterrows():

    customer_id = reply["in_response_to_tweet_id"]

    if customer_id not in tweets.index:
        continue

    customer = tweets.loc[customer_id]

    if customer["inbound"] != True:
        continue

    pairs.append({
        "customer_tweet_id": customer_id,
        "customer_text": customer["text"],
        "apple_reply_id": reply["tweet_id"],
        "apple_reply": reply["text"],
    })

pairs_df = pd.DataFrame(pairs)

print("\n=== CUSTOMER → APPLESUPPORT PAIRS ===")
print("Total pairs:", len(pairs_df))

# Random sample
sample = pairs_df.sample(
    n=min(50, len(pairs_df)),
    random_state=42
)

print("\n=== 50 RANDOM HISTORICAL PAIRS ===")

for i, (_, row) in enumerate(sample.iterrows(), start=1):

    print(f"\n{'=' * 70}")
    print(f"PAIR {i}")
    print(f"{'=' * 70}")

    print("\n[CUSTOMER]")
    print(row["customer_text"])

    print("\n[APPLE]")
    print(row["apple_reply"])
