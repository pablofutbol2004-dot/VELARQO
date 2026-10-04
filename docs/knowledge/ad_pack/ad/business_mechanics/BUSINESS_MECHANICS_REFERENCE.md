# KLEOS Business Mechanics — Reference Map

## Packs

### `offer_framing`
Owns the commercial object: buyer/problem/result definition, mechanism, scope, delivery packaging, price/term communication, risk reversal, bonuses, scarcity/urgency, and offer validation. It does **not** own price-setting or pricing-model logic.

### `pricing` (canonical home: `kleos/economics/pricing`)
Owns pricing economics and architecture: price basis, willingness to pay, cost/value bounds, pricing models and metrics, tiers, discounts/payment economics, price testing and elasticity, migrations, and pricing governance. `pricing` moved from `business_mechanics/` to `economics/` in the library expansion; the pack id is unchanged, and it is listed here only because offer/funnel/sales packs keep pricing boundaries against it.

### `funnel_mechanics`
Owns prospect state transitions: stage definitions, path/intent matching, handoffs, friction, nurture/re-entry, bottleneck diagnosis, funnel measurement, attribution caution, and scaling logic.

### `qualification`
Owns who should advance and why: fit/readiness/priority, criteria, evidence, hard/soft disqualifiers, authority, financial capacity, timing, scoring, uncertainty, routing, calibration, and qualification economics.

### `sales_conversations`
Owns interactive commercial dialogue: transparent framing, discovery/diagnosis, listening and question design, recommendation/pitch, objection clarification, proof in dialogue, explicit decision/close, context-preserving follow-up, and call-review skill calibration.

## Boundary rule
A principle lives in the pack that owns the underlying mechanism, not every surface where it appears. A pricing objection can occur in a sales call, but the economic design of the price belongs to `pricing`; the conversational handling belongs to `sales_conversations`; the displayed commercial framing belongs to `offer_framing`.
