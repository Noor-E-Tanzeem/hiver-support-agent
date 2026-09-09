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

# AppleSupport replies
apple_replies = df[
    (df["author_id"] == BRAND) &
    (df["in_response_to_tweet_id"].notna())
].copy()

# IDs of tweets AppleSupport directly replied to
customer_ids = apple_replies["in_response_to_tweet_id"].dropna()

# Find those customer tweets
customers = df[
    df["tweet_id"].isin(customer_ids) &
    (df["inbound"] == True)
].copy()

print("\n=== CUSTOMER MESSAGES APPLESUPPORT REPLIED TO ===")
print("Total:", len(customers))

# Random sample for manual inspection
sample = customers.sample(
    n=min(100, len(customers)),
    random_state=42
)

print("\n=== 100 RANDOM CUSTOMER MESSAGES ===")

for i, (_, row) in enumerate(sample.iterrows(), start=1):

    print(f"\n--- {i} ---")
    print("Tweet ID:", row["tweet_id"])
    print("Customer:", row["author_id"])
    print("Text:", row["text"])
