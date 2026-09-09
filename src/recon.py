import pandas as pd

PATH = "data/raw/twcs/twcs.csv"

print("Loading dataset...")
df = pd.read_csv(PATH)

print("\n=== BASIC INFO ===")
print("Rows:", len(df))
print("Columns:", list(df.columns))
print("Unique authors:", df["author_id"].nunique())

print("\n=== INBOUND ===")
print(df["inbound"].value_counts(dropna=False))

print("\n=== TOP AUTHORS ===")
print(df["author_id"].value_counts().head(20))

BRAND = "AppleSupport"

brand_df = df[df["author_id"] == BRAND].copy()

print(f"\n=== {BRAND} ===")
print("Tweets:", len(brand_df))
print("\nInbound/outbound:")
print(brand_df["inbound"].value_counts(dropna=False))

print("\nSample AppleSupport tweets:")
print(
    brand_df[["tweet_id", "in_response_to_tweet_id", "inbound", "text"]]
    .head(10)
    .to_string(index=False)
)

