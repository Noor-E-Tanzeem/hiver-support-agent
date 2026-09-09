from pathlib import Path
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

SOURCE_PATH = ROOT / "data" / "processed" / "apple_pairs.csv"
GOLDEN_PATH = ROOT / "data" / "processed" / "golden_set_final.xlsx"
OUTPUT_PATH = ROOT / "data" / "processed" / "apple_pairs_retrieval.csv"


def main():
    source = pd.read_csv(SOURCE_PATH)
    golden = pd.read_excel(GOLDEN_PATH)

    golden_ids = set(golden["customer_tweet_id"].astype(str))

    source_ids = source["customer_tweet_id"].astype(str)

    retrieval = source[~source_ids.isin(golden_ids)].copy()

    retrieval.to_csv(OUTPUT_PATH, index=False)

    print("Original pairs:", len(source))
    print("Golden examples:", len(golden_ids))
    print("Retrieval corpus:", len(retrieval))
    print("Golden IDs remaining:",
          retrieval["customer_tweet_id"].astype(str).isin(golden_ids).sum())
    print(f"Saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
