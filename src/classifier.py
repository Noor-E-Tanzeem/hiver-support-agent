import os
import json

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

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
apps_services = Apple apps/services such as Music, Photos, Safari, Siri, App Store, iCloud
settings_how_to = settings, configuration, feature usage, how-to questions
software_update = installing, failing, reverting, removing, or asking about updates
orders_account_billing = purchases, billing, subscriptions, reservations, account access/security, AppleCare
hardware_accessories = physical hardware or accessory problems
other_unclear = vague, incomplete, miscellaneous, thanks, greetings, resolved messages

Classify the PRIMARY support need, not merely the cause.
Example: battery drain after an update -> battery_charging.
Example: phone freezes after an update -> device_malfunction.

Escalate when the case involves:
- private account/security information or verification
- compromised account
- case-specific investigation
- potentially risky or harmful ambiguity
- a case normally requiring private/DM support

IMPORTANT ESCALATION POLICY:

Escalation is not limited to security or dangerous situations.

Escalate when resolving the customer's particular case would normally require
AppleSupport to inspect, troubleshoot, verify, or continue the case.

In particular:
- Device malfunction cases generally require escalation.
- Connectivity problems generally require escalation.
- Hardware problems generally require escalation.
- Specific app/service failures that require investigation generally require escalation.
- Battery complaints may be handled without escalation when they are simple,
  general questions, but escalate when the customer reports a specific device
  problem that needs investigation.
- Account, billing, purchase, or subscription issues generally require escalation.
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

If escalating, choose one reason:
private_account_or_security
case_specific_diagnosis
transaction_or_billing
insufficient_information
sensitive_or_risky
historical_dm_routing
other

If not escalating, escalation_reason must be "".

Return ONLY JSON:
{
  "intent": "...",
  "should_escalate": true,
  "escalation_reason": "...",
  "confidence": 0.0
}
"""


def classify(customer_text: str) -> dict:
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        temperature=0,
        max_completion_tokens=128,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": customer_text},
        ],
    )

    content = response.choices[0].message.content.strip()
    result = json.loads(content)

    if result["intent"] not in INTENTS:
        raise ValueError(f"Invalid intent: {result['intent']}")

    if not isinstance(result["should_escalate"], bool):
        raise ValueError("should_escalate must be true or false")

    if result["should_escalate"]:
        if result["escalation_reason"] not in ESCALATION_REASONS:
            raise ValueError(
                f"Invalid escalation reason: {result['escalation_reason']}"
            )
    else:
        result["escalation_reason"] = ""

    result["confidence"] = float(result["confidence"])

    if not 0 <= result["confidence"] <= 1:
        raise ValueError("confidence must be between 0 and 1")

    return result


if __name__ == "__main__":
    examples = [
        "My iPhone keeps restarting and freezing.",
        "My battery is draining very quickly after the update.",
        "I cannot connect my iPhone to Wi-Fi.",
        "I was charged for something I did not purchase.",
    ]

    for text in examples:
        print("\nCustomer:", text)
        print(json.dumps(classify(text), indent=2))
