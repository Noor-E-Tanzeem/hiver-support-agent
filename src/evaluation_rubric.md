# AI Support Agent Evaluation Rubric

## Purpose

Evaluate generated customer-support replies independently of the historical
reply text. Historical AppleSupport responses are treated as behavioral
evidence, not as gold-standard wording.

## Dimensions

Each dimension is scored from 1 to 5.

### 1. Helpfulness

**5 — Excellent**
- Directly addresses the customer's actual request.
- Provides an appropriate next step or useful answer.
- Concise and actionable.

**4 — Good**
- Addresses the request and gives a useful next step.
- Minor omissions or unnecessary wording.

**3 — Adequate**
- Partially addresses the request.
- Useful but incomplete or generic.

**2 — Poor**
- Barely addresses the request.
- Mostly generic, vague, or unhelpful.

**1 — Failing**
- Does not address the customer's request or is clearly irrelevant.

### 2. Correctness / Safety

**5 — Excellent**
- No unsupported factual claims.
- No invented policy, refund, guarantee, diagnosis, or capability.
- Advice is appropriately cautious.

**4 — Good**
- Essentially correct with only minor imprecision.

**3 — Adequate**
- No obvious harmful claim, but contains some questionable
  or insufficiently supported wording.

**2 — Poor**
- Contains a materially questionable claim or inappropriate advice.

**1 — Failing**
- Clearly false, unsafe, misleading, or fabricated.

### 3. Historical Grounding

**5 — Strongly grounded**
- Reply is clearly supported by one or more retrieved historical cases.
- The historical evidence is relevant to the actual issue or workflow.

**4 — Mostly grounded**
- Main response is supported by the evidence, with minor generic additions.

**3 — Weakly grounded**
- Some connection to the evidence exists, but the evidence is only
  moderately relevant.

**2 — Poorly grounded**
- Evidence has little relationship to the response.

**1 — Ungrounded**
- Reply contradicts, ignores, or invents information beyond the evidence,
  or relies on clearly irrelevant retrieved cases.

If no sufficiently similar historical evidence was retrieved, a concise
cautious response can still receive a reasonable grounding score if it does
not falsely claim historical support.

### 4. Escalation Fit

**5 — Correct**
- Response appropriately follows the triage escalation decision.
- If escalation is required, it clearly routes the customer appropriately.
- If escalation is not required, it does not unnecessarily route the customer
  away.

**4 — Mostly correct**
- Escalation behavior is appropriate with minor wording issues.

**3 — Ambiguous**
- Escalation direction is unclear or only partially appropriate.

**2 — Poor**
- Escalation behavior conflicts with the triage decision.

**1 — Failing**
- Clearly mishandles a case that should or should not be escalated.

### 5. Overall Quality

**5 — Production-quality**
- Helpful, correct, appropriately grounded, concise, and operationally
  appropriate.

**4 — Strong**
- Good response with minor imperfections.

**3 — Usable with review**
- Reasonable draft but needs human review/editing.

**2 — Poor**
- Significant problems make it unsuitable without substantial editing.

**1 — Unacceptable**
- Incorrect, unsafe, irrelevant, or seriously misleading.

## Important Evaluation Rules

1. Do not reward copying the historical reply verbatim.
2. Do not penalize different wording when the response preserves the useful
   historical behavior.
3. Treat retrieved examples as evidence, not ground truth.
4. Penalize invented policies, guarantees, diagnoses, refunds, or unsupported
   factual claims.
5. For private/account-specific cases, appropriate DM/private-support routing
   is generally important.
6. A response should not manufacture a troubleshooting procedure merely because
   the customer expects an answer.
7. If retrieval evidence is weak, cautious routing or a request for necessary
   information is preferable to fabricated specificity.
