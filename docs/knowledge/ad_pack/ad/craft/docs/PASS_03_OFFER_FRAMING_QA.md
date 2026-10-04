# PASS_03_OFFER_FRAMING_QA.md

## Corpus routing

- Source corpus: **11,917 transcripts**.
- Multi-concept high-signal routing for offer framing produced **1,805 candidate transcripts**.
- A weighted high-signal shortlist contained **292 transcripts**; the strongest sources were manually inspected across offer definition, value, mechanism, scope, pricing/terms, guarantees, bonuses, scarcity/urgency, and validation.
- Keyword frequency was used only for routing. Rules were promoted by semantic usefulness and cross-source support, not occurrence count.

## Source QA

- `offer_framing` rules: **44**.
- `offer_framing` categories: **9**.
- Direct `C12K` references in `offer_framing`: **88**.
- Unique transcript/timestamp anchors in `offer_framing`: **70**.
- Total `C12K` references across the updated library: **210**.
- Unique transcript/timestamp anchors across the updated library: **157**.
- Broken/missing file or timestamp references: **0**.

## Semantic duplicate QA

- General-craft packs: **14** / **241 rules**.
- Business-mechanics packs: **1** / **44 rules**.
- Total packs in current library: **15**.
- Total rules in current library: **285**.
- Exact cross-pack duplicate rule texts: **0**.
- High token-overlap cross-pack candidates (Jaccard ≥ 0.72): **0**.

## Boundary QA

- `offer_framing` does **not** contain venture-specific offers, funnel-stage design, qualification scorecards, sales scripts, proof-production rules, or format-specific execution.
- General fake-scarcity ownership was migrated/narrowed out of `cta_conversion`, `content_quality`, and `copywriting` rather than duplicated.
- Pricing rules do not encode a universal close-rate target or “always raise price” heuristic.
- Guarantees, bonuses, done-for-you delivery, and scarcity are conditional mechanisms, not mandatory offer components.
- `podcast/clip` remains removed from the roadmap.

## Rejected-universal QA

The pass explicitly did **not** promote corpus claims such as “always use a guarantee,” “more bonuses always increase value,” fixed bonus-to-price ratios, universal close-rate pricing thresholds, or fabricated urgency into canonical rules.

## Result

PASS
