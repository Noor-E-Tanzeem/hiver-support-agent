# AppleSupport Intent Annotation Guide

## Purpose

This guide defines how customer messages are labeled for the
200-example golden evaluation set.

The goal is to assign the customer's PRIMARY support intent.

Do not label based only on keywords. Label based on what the
customer is actually asking AppleSupport to help with.

---

## Intent 1: device_malfunction

Use when the main problem is that the device itself is behaving
incorrectly.

Examples:
- iPhone freezing
- phone restarting unexpectedly
- device becoming extremely slow
- apps/device crashing when the main complaint is device instability
- phone generally not working correctly

Example:
"My phone keeps freezing and restarting."

Label:
device_malfunction

---

## Intent 2: battery_charging

Use when the main problem concerns battery behavior or charging.

Examples:
- battery draining quickly
- battery health
- battery percentage
- phone not charging
- charger/charging problem
- battery becoming hot while charging

Example:
"My battery is dying really fast after the update."

Label:
battery_charging

If the message mentions an update but the customer's actual
problem is battery drain, prefer battery_charging.

---

## Intent 3: connectivity_communication

Use when the main problem concerns communication or connectivity.

Examples:
- Wi-Fi
- cellular/mobile data
- Bluetooth connectivity
- phone calls
- iMessage
- SMS/Messages
- inability to send or receive messages

Example:
"I can't send any iMessages."

Label:
connectivity_communication

---

## Intent 4: apps_services

Use when the main problem concerns an Apple application or service.

Examples:
- Apple Music
- Photos
- iCloud services
- Siri
- Safari
- App Store
- Apple service functionality

Example:
"My Apple Music library disappeared."

Label:
apps_services

If the customer is asking how to configure a setting rather than
reporting a service malfunction, use settings_how_to instead.

---

## Intent 5: settings_how_to

Use when the customer wants instructions, configuration help,
or an explanation of how a setting/feature works.

Examples:
- "How do I turn this off?"
- "Where is this setting?"
- "How do I enable this?"
- questions about how a feature behaves
- configuration questions

Example:
"How do I stop iOS from automatically downloading updates?"

Label:
settings_how_to

A message can mention iOS without being software_update.

---

## Intent 6: software_update

Use when the customer's PRIMARY request is about an operating
system/software update itself.

Examples:
- update installation failure
- update getting stuck
- update availability
- removing/reverting an update
- questions specifically about an OS update
- update-related error messages

Example:
"How do I uninstall iOS 11 and go back to iOS 10?"

Label:
software_update

If the customer says an update caused a battery problem, use
battery_charging.

If an update caused freezing/restarting and the main complaint is
the device malfunction, use device_malfunction.

---

## Intent 7: orders_account_billing

Use for account, billing, purchasing, subscription, reservation,
security, or transaction-related issues.

Examples:
- Apple account problems
- hacked/compromised account
- billing problems
- subscriptions
- purchases
- refunds/reimbursements
- reservations/orders
- activation/service transactions

Example:
"I think someone is trying to steal my Apple account information."

Label:
orders_account_billing

Security/account-compromise cases belong here and should generally
be considered for escalation.

---

## Intent 8: hardware_accessories

Use when the main problem concerns physical hardware or an accessory,
and it is not primarily a charging/battery problem.

Examples:
- damaged device
- broken screen
- defective physical hardware
- AirPods hardware problems
- physical accessories
- cables/adapters when the issue is primarily the accessory itself

Example:
"My AirPods case isn't working properly."

Label:
hardware_accessories

If the main issue is simply that the phone will not charge,
use battery_charging.

---

## Intent 9: other_unclear

Use when none of the above clearly applies.

This includes:
- greetings
- thanks
- resolved/status messages
- extremely vague complaints
- incomplete follow-up messages
- messages where the support intent cannot reasonably be determined

Examples:
"Thank you!!"
"Fixed. Cheers."
"Please fix this."

Do NOT use this category merely because the message is difficult.
Choose the most appropriate intent when the customer's intent is
reasonably clear.

---

# Multi-intent messages

Some messages contain more than one problem.

Example:
"After updating my phone, the battery drains fast and the phone freezes."

Use the PRIMARY support need.

Priority rule:

1. Identify what the customer most clearly wants help resolving.
2. If one problem is described as the main complaint, label that.
3. If two problems are equally prominent and cannot reasonably be
   prioritized, choose the intent most directly associated with the
   requested action.
4. Do not create multiple intent labels.

The annotator should record ambiguity in the notes when necessary.

---

# Cause vs. problem

Classify the SUPPORT PROBLEM, not merely the suspected cause.

Examples:

"After iOS 11, my battery drains quickly."
→ battery_charging

"iOS 11 installation keeps failing."
→ software_update

"After updating, my phone constantly freezes."
→ device_malfunction

The phrase "after the update" does not automatically mean
software_update.

---

# Follow-up messages

If the message only continues an earlier conversation and does not
contain enough information to determine a support intent, use:

other_unclear

Examples:
"More than 24 hours ago."
"6s Plus"
"Just swiping through the dates."

If the follow-up itself clearly identifies the issue, label the
corresponding intent.

---

# Escalation annotation

The golden set also contains a human label for whether the case
should be escalated.

Escalate when:

1. The case requires private account information or verification.
2. The customer reports account/security compromise.
3. The issue requires case-specific investigation that cannot safely
   be completed from the public message.
4. The issue is sufficiently ambiguous or risky that an automated
   response could reasonably cause harm or mislead the customer.
5. Historical AppleSupport behavior indicates the case is normally
   moved to DM or another support channel for further investigation.

Do not escalate solely because an issue is technically complex.

Do not escalate straightforward factual or how-to questions when
they can be answered safely and clearly.

---

# Evidence for escalation

When labeling should_escalate = true, also record a concise reason.

Allowed reason categories:

- private_account_or_security
- case_specific_diagnosis
- transaction_or_billing
- insufficient_information
- sensitive_or_risky
- historical_dm_routing
- other

The reason should describe WHY escalation is appropriate.

---

# Annotation principles

1. Label the customer's message, not Apple's response.
2. Use the customer's primary support need.
3. Do not infer facts that are not present.
4. Do not use keywords alone.
5. Prefer a specific intent over other_unclear when justified.
6. Record ambiguity rather than hiding it.
7. Keep escalation separate from intent.
8. Never assume that every difficult issue must be escalated.
9. Never invent a solution that is not supported by the evidence.
10. Apply these rules consistently across the entire golden set.
