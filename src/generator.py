import json
import re

try:
    from .llm_client import generate
except ImportError:
    from llm_client import generate


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

Return ONLY a valid JSON object.
Do not use markdown fences.
Do not add any text before or after the JSON.

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
    if not content:
        raise ValueError("Generator returned empty content")

    content = content.strip()

    content = re.sub(
        r"^```(?:json)?\s*",
        "",
        content,
    )
    content = re.sub(
        r"\s*```$",
        "",
        content,
    )

    return json.loads(content)


def _validate_result(result):
    if not isinstance(result, dict):
        raise ValueError(
            "Generator output must be a JSON object"
        )

    if "reply" not in result:
        raise ValueError(
            "Generator output missing reply"
        )

    if "grounding_evidence" not in result:
        raise ValueError(
            "Generator output missing grounding_evidence"
        )

    if not isinstance(result["reply"], str):
        raise ValueError(
            "Generator reply must be a string"
        )

    if not isinstance(result["grounding_evidence"], list):
        raise ValueError(
            "grounding_evidence must be a list"
        )

    return result


def generate_reply(
    customer_message,
    intent,
    should_escalate,
    escalation_reason,
    historical_evidence,
):
    # If retrieval found no sufficiently similar historical case,
    # do not let the LLM invent a detailed troubleshooting answer.
    # Use a conservative response instead.
    if not historical_evidence:
        if should_escalate:
            reply = (
                "We'd be happy to take a closer look. "
                "Please DM us with a few more details about the issue "
                "so we can assist you further."
            )
        else:
            reply = (
                "Thanks for reaching out. Could you share a few more "
                "details about the issue so we can better understand "
                "what you're experiencing?"
            )

        return {
            "reply": reply,
            "grounding_evidence": [
                {
                    "reason": "No sufficiently similar historical evidence was retrieved; "
                    "used a conservative information-request response.",
                    "similarity": 0.0,
                }
            ],
        }

    payload = {
        "customer_message": customer_message,
        "intent": intent,
        "should_escalate": should_escalate,
        "escalation_reason": escalation_reason,
        "historical_evidence": historical_evidence,
    }

    messages = [
        {
            "role": "system",
            "content": GENERATOR_PROMPT,
        },
        {
            "role": "user",
            "content": json.dumps(
                payload,
                ensure_ascii=False,
            ),
        },
    ]

    try:
        content = generate(
            messages,
            json_mode=True,
            max_tokens=1024,
        )

        result = _parse_json(content)

    except Exception as primary_error:
        message = str(primary_error).lower()

        is_json_constraint_failure = (
            isinstance(primary_error, json.JSONDecodeError)
            or "json_validate_failed" in message
        )

        if not is_json_constraint_failure:
            raise

        print(
            "Constrained JSON generation failed. "
            "Retrying without constrained JSON..."
        )

        fallback_content = generate(
            messages,
            json_mode=False,
            max_tokens=1024,
        )

        result = _parse_json(fallback_content)

    return _validate_result(result)


if __name__ == "__main__":
    print("Generator module loaded successfully.")
    print("API call intentionally not made.")
