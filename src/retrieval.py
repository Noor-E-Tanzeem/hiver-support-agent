from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "processed" / "apple_pairs_retrieval.csv"


class HistoricalRetriever:
    def __init__(self, data_path=DATA_PATH):
        self.df = pd.read_csv(data_path)

        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=50000,
        )

        self.matrix = self.vectorizer.fit_transform(
            self.df["customer_text"].fillna("")
        )

    def search(self, query, top_k=3, min_similarity=0.45):
        query_vector = self.vectorizer.transform([query])

        scores = cosine_similarity(
            query_vector,
            self.matrix,
        ).flatten()

        top_indices = scores.argsort()[-top_k:][::-1]

        results = self.df.iloc[top_indices].copy()
        results["similarity"] = scores[top_indices]

        results = results[
            results["similarity"] >= min_similarity
        ]

        return results[
            [
                "customer_tweet_id",
                "customer_text",
                "apple_reply_id",
                "apple_reply",
                "similarity",
            ]
        ]


if __name__ == "__main__":
    retriever = HistoricalRetriever()

    query = (
        "My iPhone battery is draining very quickly "
        "after the latest update."
    )

    results = retriever.search(query, top_k=3)

    if results.empty:
        print("No sufficiently similar historical cases found.")
    else:
        for _, row in results.iterrows():
            print("\n---")
            print("Similarity:", round(row["similarity"], 3))
            print("Customer:", row["customer_text"])
            print("AppleSupport:", row["apple_reply"])
