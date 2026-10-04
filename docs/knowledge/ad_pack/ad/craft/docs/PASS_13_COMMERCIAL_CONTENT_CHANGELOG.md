# Pass 13 — Commercial Content changelog

## Added

- Five general-craft packs under `kleos/craft/`: `commercial_content_strategy` (20 rules), `buyer_awareness` (15), `belief_change` (12), `objection_handling` (14), `trust_authority` (18) — 79 rules total.
- Five pack reference documents, one per pack.
- `PASS_13_COMMERCIAL_CONTENT_ARCHITECTURE.md`.
- Regenerated `GENERAL_CRAFT_REFERENCE.md` (now 19 general packs / 316 rules).

## Migrated (dedupe)

- Generic in-flow objection rule: `copywriting` → `objection_handling`.
- Authority-cue rule: `proof` → `trust_authority`.
- Observed-customer objection sourcing rule: `vsl` → `objection_handling` (the VSL-specific asynchronous objection-placement rule stays in `vsl`).

## Deliberately not created

- `demand_creation`, `identity`, and `positioning_mechanism` were evaluated and not made standalone packs; see `PASS_13_COMMERCIAL_CONTENT_ARCHITECTURE.md`. `content_that_sells` remains an umbrella question, not a pack.

## Wiring

- `buyer_awareness` added to the Strategy phase (`PHASE_PACKS["strategy"]`) so audience-awareness craft is composed when choosing what to make.
- Remaining packs stay composed-by-name; the default phase bundles are at their craft budget.
