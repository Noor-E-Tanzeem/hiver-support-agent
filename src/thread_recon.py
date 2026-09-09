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
    ],
)

# Use tweet_id as the lookup key.
tweets = df.set_index("tweet_id")

apple = df[df["author_id"] == BRAND].copy()

print("\n=== APPLESUPPORT REPLIES ===")
print("Total AppleSupport tweets:", len(apple))
print(
    "AppleSupport replies:",
    apple["in_response_to_tweet_id"].notna().sum()
)

def get_thread(tweet_id, max_hops=30):
    """
    Walk backwards from a tweet to the earliest
    linked tweet that exists in the dataset.
    """
    thread = []
    current_id = tweet_id
    seen = set()

    while (
        pd.notna(current_id)
        and current_id in tweets.index
        and current_id not in seen
        and len(thread) < max_hops
    ):
        seen.add(current_id)

        row = tweets.loc[current_id]

        thread.append({
            "tweet_id": current_id,
            "author_id": row["author_id"],
            "inbound": row["inbound"],
            "text": str(row["text"]),
            "created_at": row["created_at"],
        })

        current_id = row["in_response_to_tweet_id"]

    return list(reversed(thread))


# Sample AppleSupport replies.
apple_replies = apple[
    apple["in_response_to_tweet_id"].notna()
]

sample_size = min(300, len(apple_replies))

sample = apple_replies.sample(
    n=sample_size,
    random_state=42
)

threads = []

for tweet_id in sample["tweet_id"]:
    thread = get_thread(tweet_id)

    if len(thread) >= 3:
        threads.append(thread)


print("\n=== THREAD LENGTHS ===")

lengths = pd.Series([len(t) for t in threads])

if len(lengths) > 0:
    print("Threads with >=3 messages:", len(lengths))
    print("Mean:", round(lengths.mean(), 2))
    print("Median:", lengths.median())
    print("Max:", lengths.max())
    print("\nDistribution:")
    print(lengths.value_counts().sort_index())
else:
    print("No multi-message threads found.")


print("\n=== SAMPLE MULTI-TURN THREADS ===")

for i, thread in enumerate(threads[:5], start=1):

    print(f"\n{'=' * 70}")
    print(f"THREAD {i} — {len(thread)} messages")
    print(f"{'=' * 70}")

    for msg in thread:

        if msg["inbound"]:
            speaker = "CUSTOMER"
        else:
            speaker = "APPLE"

        print(f"\n[{speaker}]")
        print(msg["text"])
