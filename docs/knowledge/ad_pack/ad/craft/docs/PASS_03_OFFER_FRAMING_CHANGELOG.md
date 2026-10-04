# PASS_03_OFFER_FRAMING_CHANGELOG.md

## Added

- Added `kleos/business_mechanics/offer_framing/essentials.yaml` with **44 rules across 9 categories**.
- Added `OFFER_FRAMING_REFERENCE.md`.
- Added `BUSINESS_MECHANICS_REFERENCE.md`.
- Added source-level QA and cross-pack duplicate QA.

## Migrated / narrowed

- **`cta_conversion`:** removed generic fabricated-scarcity language from the CTA ethics rule; truthful commercial scarcity/urgency now belongs to `offer_framing`.
- **`content_quality`:** narrowed the generic fabrication rule to content facts/stories/science/results so offer-level urgency is not duplicated.
- **`copywriting`:** narrowed unsupported-persuasion examples so commercial urgency/scarcity is owned by `offer_framing` rather than sentence-level craft.

## Scope decisions

- Actual offers remain in each business's offer graph; this pack contains reusable mechanics only.
- Guarantees, bonuses, scarcity, higher pricing, and done-for-you delivery are modeled as conditional tools rather than universal upgrades.
- Offer attractiveness is evaluated together with fulfillment load, margin, refunds, retention, and customer outcomes.
- `podcast/clip` remains removed from scope.

## Next pass

- `funnel_mechanics`
