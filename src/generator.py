import json
import re

try:
    from .llm_client import client, LLM_MODEL
except ImportError:
    from llm_client import client, LLM_MODEL


GENERATOR_PROMPT = """
You are an AppleSupport response drafting assistant.

Draft a concise, helpful response to the customer's CURRENT message.

Use the historical AppleSupport examples as behavioral evidence:
- Prefer approaches AppleSupport actually used for similar cases.
- Do not blindly copy a historical reply.
- Do not invent Apple policies, refunds, guarantees, diagnoses, or unsupported facts.
- Do not expose private information.
- If the case should be escalated, clearly direct the customer to private support/DM when appropriate.
- If the historical evidence is weak or unrelated, say less rather than inventing details.
- Answer the customer's actual request, not just keywords.

The intent and escalation decision have already been determined by the triage system.
Respect them.

Return ONLY a JSON object. Do not use markdown fences.

The JSON must have exactly this structure:
{
  "reply": "customer-facing response",
  "grounding_evidence": [
    {
      "reason": "brief explanation of which historical example influenced the reply",
      "similarity": 0.0
    }
  ]
}
"""


def _parse_json(content):
    content = content.strip()

    # Remove accidental markdown code fences if the model adds them.
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    return json.loads(content)


def generate_reply(
    customer_message,
    intent,
    should_escalate,
    escalation_reason,
    historical_evidence,
):
    payload = {
        "customer_message": customer_message,
        "intent": intent,
        "should_escalate": should_escalate,
        "escalation_reason": escalation_reason,
        "historical_evidence": historical_evidence,
    }

    response = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        max_completion_tokens=256,
        messages=[
            {"role": "system", "content": GENERATOR_PROMPT},
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False),
            },
        ],
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("Generator returned empty content")

    result = _parse_json(content)

    if not isinstance(result, dict):
        raise ValueError("Generator output must be a JSON object")

    if "reply" not in result:
        raise ValueError("Generator output missing reply")

    if "grounding_evidence" not in result:
        raise ValueError("Generator output missing grounding_evidence")

    if not isinstance(result["reply"], str):
        raise ValueError("Generator reply must be a string")

    if not isinstance(result["grounding_evidence"], list):
        raise ValueError("grounding_evidence must be a list")

    return result


if __name__ == "__main__":
    print("Generator module loaded successfully.")
    print("API call intentionally not made.")
