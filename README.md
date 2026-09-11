# Hiver SDE Intern Take-Home — AI Support Agent

## 1. What I built

I built an AI support agent for AppleSupport using the Customer Support on Twitter (TWCS) dataset.

For an incoming customer message, the system:

1. predicts the main support intent,
2. decides whether the case should be auto-handled or escalated,
3. retrieves similar historical AppleSupport interactions,
4. drafts a reply using those interactions as evidence.

I focused on the support decision pipeline and evaluation rather than building a production Twitter/X interface.

## 2. Dataset and brand choice

I used the Customer Support on Twitter (TWCS) dataset by thoughtvector from Kaggle.

After reconstructing customer/reply pairs:

- 106,646 AppleSupport customer/reply pairs
- 106,623 unique customer messages
- 106,860 AppleSupport tweets in the original dataset

The raw dataset is not committed to this repository.

## 3. What good means

A good support agent should:

- identify the customer's primary support need,
- escalate cases that require private access or case-specific investigation,
- avoid unnecessary escalation for straightforward questions,
- use historical support behavior as evidence,
- avoid inventing policies, refunds, guarantees, diagnoses, or unsupported facts,
- remain conservative when useful historical evidence is unavailable.

## 4. Intent taxonomy

I defined nine support intents:

| Intent | Meaning |
|---|---|
| device_malfunction | Freezing, crashing, restarting, slowness, device instability |
| battery_charging | Battery drain, battery percentage, charging problems |
| connectivity_communication | Wi-Fi, cellular, Bluetooth, calls, iMessage/SMS |
| apps_services | Apple apps and services such as Music, Photos, Safari, Siri, App Store and iCloud |
| settings_how_to | Settings, configuration, feature usage and how-to questions |
| software_update | Update installation, failure, availability, removal or reverting |
| orders_account_billing | Purchases, billing, subscriptions, account/security and AppleCare |
| hardware_accessories | Physical hardware and accessory problems |
| other_unclear | Vague, incomplete, miscellaneous, greetings, thanks and resolved messages |

The classifier uses the primary support need rather than simply the cause mentioned in the message.

## 5. Escalation

Possible escalation reasons:

- private_account_or_security
- case_specific_diagnosis
- transaction_or_billing
- insufficient_information
- sensitive_or_risky
- historical_dm_routing
- other

Cases involving account/security issues, billing or transactions, and case-specific investigation generally require escalation.

Straightforward settings/how-to questions generally do not.

## 6. Pipeline

```text
Customer message
       |
       v
Intent + Escalation Classifier
       |
       +--------------------+
       |                    |
       v                    v
intent/escalation     Historical Retrieval
                            |
                            v
                    Similar AppleSupport cases
                            |
                            v
                     Response Generator
                            |
                            v
                    Reply + Evidence


Current model: openai/gpt-oss-20b through Groq.

## 7. Golden evaluation set

I created a 5,000-example development set.

The final golden evaluation set contains 200 hand-labelled examples.

Sampling:

15 coverage examples from each of 8 major intent groups = 120

80 additional random examples


The coverage groups were:

battery/charging

software update

connectivity

apps/services

orders/account/billing

hardware/accessories

settings/how-to

device malfunction


Development examples were excluded from the golden pool.

Golden customer messages were also excluded from the retrieval corpus to reduce evaluation leakage.

Golden set:

data/processed/golden_set_final.xlsx

## 8. Intent classification results

Evaluation set: 200 examples.

Metric	Result

Accuracy	77.5%
Macro-F1	73.1%


Test-set majority-intent sanity baseline: 23.0% accuracy.

Intent	Precision	Recall	F1

apps_services	0.85	0.54	0.66
battery_charging	0.90	0.97	0.93
connectivity_communication	0.56	1.00	0.72
device_malfunction	0.89	0.85	0.87
hardware_accessories	0.79	0.92	0.85
orders_account_billing	0.91	0.81	0.86
other_unclear	0.68	0.62	0.65
settings_how_to	0.53	0.75	0.62
software_update	0.30	0.75	0.43


## 9. Escalation results

Evaluation set: 200 examples.

Metric	Result

Accuracy	83.5%
Macro-F1	72.9%
Escalation F1      89.8%


Majority-escalation baseline: 79.0% accuracy.

Confusion matrix:

Predicted
                 no     yes
Actual no        21      21
Actual yes       12     146

The model catches most human-labelled escalation cases, but it is conservative and over-escalates some cases.

## 10. Retrieval

I used TF-IDF retrieval because it is simple, deterministic, inexpensive and easy to inspect.

Configuration:

lowercase text

English stop-word removal

unigrams + bigrams

maximum 50,000 features

cosine similarity


An initial similarity threshold of 0.45 was used.

Threshold	Coverage

0.30	90.0%
0.40	53.5%
0.45	37.0%
0.50	26.5%
0.55	18.5%
0.60	12.5%


At 0.45, 74/200 examples had at least one retrieved case.

This is retrieval coverage, not retrieval accuracy.

Qualitative inspection showed that lexical overlap can still produce bad precedents. For example, an accidental in-app purchase query retrieved an unrelated headphone-warranty case.

## 11. Response generation

The generator receives:

customer message

predicted intent

escalation decision

escalation reason

retrieved historical cases


Historical replies are treated as behavioral evidence rather than text to copy.

The generator is instructed not to invent policies, refunds, guarantees, diagnoses or unsupported facts.

There is also a deterministic no-evidence fallback.

If no sufficiently similar historical evidence is retrieved, the system returns a conservative information-request or private-support response instead of asking the LLM to invent detailed troubleshooting.

This reduces hallucinated troubleshooting, although it can make some replies less helpful.

## 12. Generation evaluation

Generation was completed for 60 of the 200 golden examples because the provider daily token quota was reached.

This subset is not claimed to be a statistically representative generation benchmark.

Intent	Count

apps_services	14
device_malfunction	11
orders_account_billing	9
battery_charging	8
other_unclear	7
settings_how_to	5
hardware_accessories	3
connectivity_communication	2
software_update	1


Historical retrieval was available for 20/60 examples.

No sufficiently similar evidence was available for 40/60 examples.

Results:

data/processed/generation_predictions.csv

I did not claim a human-grounded response-quality metric because there is no human-labelled gold standard for ideal reply wording. The LLM-as-judge harness was implemented as a secondary quality assessment, but the attempted run was interrupted by provider quota limits, so no aggregate judge metric is reported.

## 13. LLM-as-judge

I implemented an LLM-as-judge evaluation harness and rubric and attempted a deterministic 20-example evaluation sample from the clean 60-example generation evaluation set. The run was interrupted by the provider token-per-day quota after one example was successfully judged, so I do not report aggregate judge scores or human-agreement statistics.

The judge scored each response from 1–5 on:

- **Helpfulness** — does the reply meaningfully address the customer's request?
- **Correctness / Safety** — is it factually safe and free of unsupported claims?
- **Historical Grounding** — does it appropriately use the retrieved historical evidence when evidence is available?
- **Escalation Fit** — is the response consistent with whether the case should be handled publicly or routed for further support?
- **Overall Quality** — overall usefulness and appropriateness of the response.

The judge was instructed not to reward verbatim copying of historical replies. Historical responses were treated as evidence of how AppleSupport handled similar cases, not as a gold response that must be reproduced exactly.

The rubric also explicitly penalizes invented troubleshooting, diagnoses, refunds, guarantees, policies, or other unsupported claims. When historical evidence is weak or unavailable, a cautious request for more information or appropriate routing is preferred.

The planned 20-example sample was selected deterministically from the clean generation set, with coverage across escalation decisions and retrieval availability. Human labels were kept separate from the judge's input. Because the run did not complete, no judge-versus-human agreement statistic is claimed.

This evaluation is intended as a qualitative/secondary evaluation of response quality rather than a replacement for the hand-labelled golden-set evaluation. The classifier metrics on all 200 golden examples remain the primary quantitative benchmark.

## 14. Baselines

Majority intent

Always predict the most common intent.

Accuracy: 23.0%

Agent:

Accuracy: 77.5%

Macro-F1: 73.1%


Majority escalation

Always escalate.

Accuracy: 79.0%

Agent:

Accuracy: 83.5%

Macro-F1: 72.9%

Escalation recall: 92.4%


This is why escalation accuracy alone is not enough.

Simple historical-response baseline

Retrieve the highest-TF-IDF historical example and return its AppleSupport reply if similarity is at least 0.45.

Retrieval coverage: 37.0% on the golden set.

I did not claim that returning a similar historical reply is automatically high quality. A proper response-quality comparison needs human response labels.

## 15. Top failure modes

1. Over-escalation

There were 42 human-labelled non-escalation examples, and the model incorrectly escalated 21.

Hypothesis: the escalation prompt strongly prioritizes safety and case-specific investigation, so the model chooses escalation when uncertain.

Next step: add more hard-negative examples where difficult-looking questions are still safe to answer.

2. Update/iOS keyword anchoring

The model sometimes predicts software_update because words such as update or iOS appear even when the main problem is an app, device, battery or settings issue.

Hypothesis: the model follows a visible cause word instead of the primary-support-need rule.

Next step: add contrastive examples such as battery + update -> battery and freezing + update -> device malfunction.

3. TF-IDF retrieval mistakes

TF-IDF can retrieve cases with similar vocabulary but different support meaning.

Example: an accidental in-app purchase query retrieved a headphone-warranty case.

Hypothesis: bag-of-words similarity does not understand support semantics.

Next step: use semantic embeddings followed by a reranker.

4. Safe fallback can be too generic

When there is no useful historical evidence, the system avoids inventing troubleshooting.

This is safer but can be less helpful for straightforward questions.

Example: a Mac Mail settings problem received an information-request response because no sufficiently similar historical case was retrieved.

Hypothesis: the current safety rule treats lack of historical evidence as lack of permission to generate an answer.

Next step: add a trusted general knowledge source for simple how-to questions.

5. Missing conversational context

The classifier currently receives one customer message.

Some TWCS messages are fragments or follow-ups whose meaning depends on previous messages.

Hypothesis: useful information is lost before classification and retrieval.

Next step: reconstruct the conversation thread and pass a bounded recent context window.

## 16. What is misleading about my headline number?

The headline classifier accuracy of 77.5% is useful, but it should not be read as a production-ready quality estimate.

Important limitations:

- coverage sampling rather than natural traffic distribution
- several small intent classes
- `software_update` has only 4 golden examples, so its 0.43 F1 is not a stable estimate — a single misclassification shifts the score substantially
- historical Twitter data
- single-message classification
- escalation accuracy only modestly above the 79% majority baseline
- generation evaluated on only 60/200 examples
- judge benchmark incomplete
- retrieval coverage is not retrieval correctness
- results depend on the selected LLM and prompt

All 200 golden examples were annotated by a single person; no inter-annotator agreement was measured, so individual labelling judgment may introduce some label noise.

The most defensible conclusion is:

> On this 200-example golden set, the classifier substantially outperforms the majority intent baseline and catches most human-labelled escalation cases, but retrieval and generation need stronger independent evaluation before production use.

## 17. What I did not build

This is a take-home prototype, not a production support platform.

Not built:

live Twitter/X integration

customer account lookup

actual DM sending

refunds or transaction actions

production vector database

semantic reranking

persistent conversation state

human-agent UI

online learning

automatic policy synchronization

complete multilingual support

production latency/cost optimization

full safety red-team testing


## 18. Reproducing the project

Requirements:

Python 3.10+

Groq API key

TWCS dataset


Install:

pip install -r requirements.txt

Create .env:

cp .env.example .env

Add the Groq API key.

Place the dataset at:

data/raw/twcs/twcs.csv

Build AppleSupport pairs:

python src/build_pairs.py

Create development data:

python src/create_dev_set.py

Create golden candidates:

python src/create_golden_candidates.py

Build retrieval corpus:

python src/create_retrieval_corpus.py

Run classifier evaluation:

python src/evaluate_classifier.py

Run generation evaluation:

python src/evaluate_generation.py --limit 60

Run the judge:

python src/evaluate_judge.py --sample 20

The saved prediction files allow the reported classifier results to be inspected without rerunning every API call.

## 19. Running the agent

After configuring .env:

from src.agent import run_agent

result = run_agent(
    "My iPhone keeps freezing after the latest update."
)

print(result)

The result contains:

customer_message

intent

should_escalate

escalation_reason

classifier_confidence

reply

grounding_evidence

retrieved_cases


## 20. Decision log

1. Selected AppleSupport because it has a large number of interactions and useful historical support replies.


2. Focused on evaluation before UI because the assignment emphasizes proving that the system works.


3. Used nine intents so the taxonomy is small enough to evaluate manually while covering the main support patterns.


4. Classified primary need rather than cause so an update mention does not automatically become software_update.


5. Created a separate 5,000-example development set.


6. Used 200 golden examples because this fits the requested range.


7. Mixed coverage sampling with random sampling so smaller intents are represented.


8. Included escalation labels because deciding whether the AI should act is a core part of the assignment.


9. Removed golden customer messages from the retrieval corpus to reduce exact-example leakage.


10. Started with TF-IDF because it is transparent and easy to inspect.


11. Used a 0.45 retrieval threshold as an initial conservative trade-off.


12. Added structured JSON validation instead of trusting raw LLM output.


13. Added a deterministic no-evidence fallback after observing that the LLM could invent detailed troubleshooting without supporting evidence.


14. Checkpointed API evaluation so quota failures would not discard completed results.


15. Did not report a judge metric from one successful judgment because that would give a false impression of evaluation quality.



## 21. Next week

With another week, I would:

1. add conversation/thread context,


2. replace TF-IDF with semantic embeddings,


3. add a retrieval reranker,


4. add a trusted general knowledge source for simple how-to questions,


5. add more difficult non-escalation examples,


6. add contrastive examples for update/cause confusion,


7. run a larger generation evaluation,


8. complete the LLM-as-judge evaluation,


9. add human response-quality labels,


10. measure latency, token usage and failure rates.



Attribution

Dataset: Customer Support on Twitter (TWCS)

Author: thoughtvector

Source: Kaggle

The raw dataset is excluded from Git because of its size and is expected to be downloaded separately.
