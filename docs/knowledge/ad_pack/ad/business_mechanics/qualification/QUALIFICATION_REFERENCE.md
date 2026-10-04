# KLEOS Qualification — Reference Map

## Ownership
`qualification` owns the decision logic for who should advance, when, and why: fit criteria, disqualifiers, readiness, authority, financial ability, evidence collection, scoring, uncertainty, routing, calibration, and qualification economics.

It does **not** own:
- the wording/tone of live discovery or objection handling (`sales_conversations`);
- where the application or routing step appears in the customer journey (`funnel_mechanics`);
- the commercial promise, price, guarantee, or scope (`offer_framing`);
- the persuasive expression of an ask (`cta_conversion`).

## Core model
Qualification is best represented as three related but distinct layers:

1. **Fit** — can this specific offer plausibly help this prospect, and can the business serve them successfully?
2. **Readiness** — are the necessary conditions present for them to act now (timing, authority path, finances, operational capacity, etc.)?
3. **Priority** — given scarce sales/operational attention, how urgently should this opportunity be worked relative to others?

A binary qualified/unqualified field may be useful operationally, but it should be derived from these underlying states rather than replacing them.

## Categories
- `qualification_definition_and_states` — what qualification means and how fit/readiness/priority differ.
- `criteria_design_and_governance` — deriving, documenting, and standardizing criteria.
- `fit_dimensions` — problem, priority, serviceability, finances, authority, timing, implementation constraints, success fit.
- `evidence_and_question_design` — gathering only the evidence needed for the decision.
- `scoring_and_uncertainty` — soft scoring, hard gates, conflicting evidence, manual review.
- `routing_and_disqualification` — mapping states to next actions.
- `calibration_and_feedback` — false positives/negatives and downstream learning.
- `measurement_and_economics` — qualified volume, cost, reasons, capacity, downstream economics.

## Deliberate corrections to corpus advice
The corpus contains many useful qualification patterns, but several recurring claims were intentionally **not** promoted to durable rules:
- BANT (or any named acronym) is not a universal definition of qualification.
- A fixed revenue, income, credit, budget, or timing cutoff is not inherently correct across offers.
- More application questions do not automatically mean better leads.
- More friction does not automatically create more intent.
- A non-decision-maker is not always worthless; they can be a connector or champion.
- 'Not ready now' is not the same state as 'bad fit'.
- AI enrichment and lead-score vendors provide evidence, not ground truth.
- A high disqualification rate is not a goal by itself.

## Date sensitivity
The core qualification principles are durable. Specific CRM features, advertising-platform conversion APIs, enrichment vendors, credit-data products, privacy rules, and automated routing implementations are operational details and should be re-checked before implementation.
