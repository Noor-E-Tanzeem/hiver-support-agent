import json

from classifier import classify
from retrieval import HistoricalRetriever


retriever = HistoricalRetriever()


def build_evidence(results):
    evidence = []

    for _, row in results.iterrows():
        evidence.append({
            "customer_example": row["customer_text"],
            "historical_reply": row["apple_reply"],
            "similarity": round(float(row["similarity"]), 3),
        })

    return evidence


def prepare_agent_input(customer_text, top_k=3):
    classifier_result = classify(customer_text)

    results = retriever.search(
        customer_text,
        top_k=top_k,
        min_similarity=0.45,
    )

    evidence = build_evidence(results)

    return {
        "customer_message": customer_text,
        "intent": classifier_result["intent"],
        "should_escalate": classifier_result["should_escalate"],
        "escalation_reason": classifier_result["escalation_reason"],
        "classifier_confidence": classifier_result["confidence"],
        "historical_evidence": evidence,
    }


if __name__ == "__main__":
    print("Agent module loaded successfully.")
    print("Retriever initialized successfully.")
    print("API call intentionally not made.")
