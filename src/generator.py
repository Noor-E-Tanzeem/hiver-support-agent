import os
import json

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])


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

Return ONLY valid JSON:

{
  "reply": "...",
  "grounding_evidence": [
    {
      "reason": "brief explanation of which historical example influenced the reply",
      "similarity": 0.0
    }
  ]
}
"""


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
        model="openai/gpt-oss-20b",
        temperature=0,
        max_completion_tokens=256,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": GENERATOR_PROMPT},
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False),
            },
        ],
    )

    result = json.loads(
        response.choices[0].message.content.strip()
    )

    if "reply" not in result:
        raise ValueError("Generator output missing reply")

    if "grounding_evidence" not in result:
        raise ValueError("Generator output missing grounding_evidence")

    return result


if __name__ == "__main__":
    print("Generator module loaded successfully.")
    print("API call intentionally not made.")
