import os
import json
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

client = Groq(api_key=os.environ["GROQ_API_KEY"])


INTENTS = [
    "device_malfunction",
    "battery_charging",
    "connectivity_communication",
    "apps_services",
    "settings_how_to",
    "software_update",
    "orders_account_billing",
    "hardware_accessories",
    "other_unclear",
]


ESCALATION_REASONS = [
    "private_account_or_security",
    "case_specific_diagnosis",
    "transaction_or_billing",
    "insufficient_information",
    "sensitive_or_risky",
    "historical_dm_routing",
    "other",
]


SYSTEM_PROMPT = """
You classify AppleSupport customer messages.

Choose exactly one intent:

device_malfunction = freezing, crashing, restarting, slowness, device instability

battery_charging = battery drain, battery percentage, charging problems

connectivity_communication = Wi-Fi, cellular, Bluetooth, calls, iMessage/SMS

apps_services = Apple apps/services such as Music, Photos, Safari, Siri,
App Store, iCloud

settings_how_to = settings, configuration, feature usage, how-to questions

software_update = installing, failing, reverting, removing, or asking about
updates

orders_account_billing = purchases, billing, subscriptions, reservations,
account access/security, AppleCare

hardware_accessories = physical hardware or accessory problems

other_unclear = vague, incomplete, miscellaneous, thanks, greetings,
resolved messages

Classify the PRIMARY support need, not merely the cause.

Examples:
- battery drain after an update -> battery_charging
- phone freezes after an update -> device_malfunction
- an Apple app/service malfunction -> apps_services
- a purchase, billing, or subscription problem -> orders_account_billing


ESCALATION POLICY:

Escalation is not limited to security or dangerous situations.

Escalate when resolving the customer's particular case would normally require
AppleSupport to inspect, troubleshoot, verify, or continue the case.

In particular:
- Device malfunction cases generally require escalation.
- Connectivity problems generally require escalation.
- Hardware problems generally require escalation.
- Specific app/service failures that require investigation generally require
  escalation.
- Battery complaints may be handled without escalation when they are simple,
  general questions, but escalate when the customer reports a specific device
  problem that needs investigation.
- Account, billing, purchase, or subscription issues generally require
  escalation.
- Vague or incomplete messages should be escalated when there is not enough
  information to safely determine the appropriate support response.
- Straightforward settings/how-to questions should generally NOT be escalated.
- Simple factual questions that can be answered without case-specific
  investigation should generally NOT be escalated.

Use the historical support workflow as the deciding factor:
if resolving the customer's particular case would normally require AppleSupport
to inspect, troubleshoot, verify, or continue the case privately, escalate it.

Do not assume "no escalation" merely because a generic troubleshooting step
could be suggested.

If escalating, choose exactly one reason:
private_account_or_security
case_specific_diagnosis
transaction_or_billing
insufficient_information
sensitive_or_risky
historical_dm_routing
other

If not escalating, escalation_reason must be "".

Confidence must be a number from 0.0 to 1.0.

Return ONLY a JSON object.
Do not use Markdown code fences.
Do not add explanations before or after the JSON.

Use exactly this structure:

{
  "intent": "one allowed intent",
  "should_escalate": true,
  "escalation_reason": "one allowed reason",
  "confidence": 0.0
}
"""


def _parse_json(content):
    content = content.strip()

    # Remove accidental Markdown code fences.
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    return json.loads(content)


def classify(customer_text: str) -> dict:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        temperature=0,
        max_completion_tokens=512,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": customer_text},
        ],
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("Classifier returned empty content")

    result = _parse_json(content)

    if not isinstance(result, dict):
        raise ValueError("Classifier output must be a JSON object")

    required_fields = [
        "intent",
        "should_escalate",
        "escalation_reason",
        "confidence",
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(f"Classifier output missing {field}")

    if result["intent"] not in INTENTS:
        raise ValueError(
            f"Invalid intent: {result['intent']}"
        )

    if not isinstance(result["should_escalate"], bool):
        raise ValueError(
            "should_escalate must be true or false"
        )

    if result["should_escalate"]:
        if result["escalation_reason"] not in ESCALATION_REASONS:
            raise ValueError(
                f"Invalid escalation reason: "
                f"{result['escalation_reason']}"
            )
    else:
        result["escalation_reason"] = ""

    result["confidence"] = float(result["confidence"])

    if not 0 <= result["confidence"] <= 1:
        raise ValueError(
            "confidence must be between 0 and 1"
        )

    return result


if __name__ == "__main__":
    print("Classifier module loaded successfully.")
    print("API call intentionally not made.")
