from retrieval import HistoricalRetriever


def baseline_response(customer_text, min_similarity=0.45):
    retriever = HistoricalRetriever()

    results = retriever.search(
        customer_text,
        top_k=1,
        min_similarity=min_similarity,
    )

    if results.empty:
        return {
            "reply": "Thanks for reaching out. Could you provide more details about the issue?",
            "similarity": 0.0,
            "source": "fallback",
        }

    row = results.iloc[0]

    return {
        "reply": row["apple_reply"],
        "similarity": round(float(row["similarity"]), 3),
        "source": "top_historical_reply",
        "customer_example": row["customer_text"],
    }


if __name__ == "__main__":
    query = (
        "My iPhone battery is draining very quickly "
        "after the latest update."
    )

    result = baseline_response(query)

    print("=== RESPONSE BASELINE ===")
    print("Reply:", result["reply"])
    print("Similarity:", result["similarity"])
    print("Source:", result["source"])
