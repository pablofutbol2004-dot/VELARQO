# Pass 13 — Commercial Content Architecture Audit

## Umbrella decision

`content_that_sells` is an umbrella research question, **not** a canonical pack. The pass routes durable principles into the pack that owns the underlying mechanism.

## New packs created

- `commercial_content_strategy` — portfolio jobs, sequencing, qualified attention, message-to-offer continuity, market feedback.
- `buyer_awareness` — diagnosis and message matching by what the buyer currently understands.
- `belief_change` — diagnosis and evidence-backed replacement of commercially relevant buyer models.
- `objection_handling` — reusable objection discovery, prioritization, and non-interactive resolution.
- `trust_authority` — accumulated source competence, credibility, reputation, associations, and affinity.

## Candidate packs deliberately NOT created

- `demand_creation` — not created as a separate pack. Demand creation vs demand capture lives as a strategy category in `commercial_content_strategy`, while awareness-state and belief-update mechanics remain in `buyer_awareness` and `belief_change`.
- `identity` — treated as a possible relevance/affinity/belief mechanism, not enough distinct durable mechanics for a standalone pack in this corpus pass.
- `positioning_mechanism` — product mechanism/differentiation remains in `offer_framing`; source associations live in `trust_authority`. A future broad brand-positioning pack can be considered only if a dedicated corpus pass exposes missing primitives.

## Existing packs retained as owners

- `proof` — claim-specific evidence.
- `qualification` — fit/readiness/priority classification.
- `cta_conversion` — requested next action.
- `offer_framing` — buyer/problem/result/mechanism/terms of the offer.
- `funnel_mechanics` — journey states, paths, handoffs, nurture, bottlenecks.
- `content_measurement` — metrics, experiments, and performance diagnosis.
- `copywriting` — sentence/argument expression mechanics, not objection strategy.
- `sales_conversations` — interactive commercial dialogue and live objection diagnosis.

## Migrations (dedupe)

- Copywriting → objection handling: strongest believable objection in-flow rule.
- Proof → trust & authority: credentials/awards/longevity/notable clients as authority cues.
- VSL → objection handling: derive objection coverage from observed customer evidence.

## Wiring note

`buyer_awareness` is loaded by the Strategy phase (`PHASE_PACKS["strategy"]`). The other four packs are general craft composed on demand by name/category when a piece has a commercial job; the default phase bundles are already at their craft budget, so they are not force-appended.
