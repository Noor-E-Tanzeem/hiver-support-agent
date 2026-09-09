import json

try:
    from .classifier import classify
    from .generator import generate_reply
    from .retrieval import HistoricalRetriever
except ImportError:
    from classifier import classify
    from generator import generate_reply
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


def run_agent(customer_text, top_k=3):
    # 1. Classify and decide escalation.
    classifier_result = classify(customer_text)

    # 2. Retrieve historically similar AppleSupport cases.
    results = retriever.search(
        customer_text,
        top_k=top_k,
        min_similarity=0.45,
    )

    evidence = build_evidence(results)

    # 3. Draft a response grounded in the retrieved evidence.
    generated = generate_reply(
        customer_message=customer_text,
        intent=classifier_result["intent"],
        should_escalate=classifier_result["should_escalate"],
        escalation_reason=classifier_result["escalation_reason"],
        historical_evidence=evidence,
    )

    # 4. Return one clean agent output.
    return {
        "customer_message": customer_text,
        "intent": classifier_result["intent"],
        "should_escalate": classifier_result["should_escalate"],
        "escalation_reason": classifier_result["escalation_reason"],
        "classifier_confidence": classifier_result["confidence"],
        "reply": generated["reply"],
        "grounding_evidence": generated["grounding_evidence"],
        "retrieved_cases": evidence,
    }


if __name__ == "__main__":
    print("Agent module loaded successfully.")
    print("Retriever initialized successfully.")
    print("API call intentionally not made.")
