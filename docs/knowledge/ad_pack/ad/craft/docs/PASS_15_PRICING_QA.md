# Pass 15 — Pricing QA

## Structural
- Pricing rules: **49**
- Categories: **8**
- Library packs after pass: **30**
- Library rules after pass: **901**
- YAML parse failures: **0**

## Corpus provenance
- Direct C12K references in pricing pack: **94**
- Unique C12K anchors: **67**
- Unique source transcripts represented: **15**
- Missing transcript/timestamps: **0**

## Duplication
- Exact cross-pack duplicate rules: **0**
- High-overlap pricing-vs-existing candidates at 0.92 similarity: **0**

## Migration QA
- `offer_framing/pricing_and_terms` removed.
- Price-setting, market comparison, close-rate signal, capacity pricing, payment economics, and reciprocal discount logic migrated to `pricing`.
- `offer_framing` retains only price/term communication mechanics, including decision-load and truthful anchoring.

## Rejected absolutes
- no universal markup or close-rate target
- no “always value-price” rule
- no “raise until complaints” rule
- no universal lifetime-deal/subscription/performance-pricing rule
- no universal number of tiers or payment options
- no automatic grandfathering rule

## Source failures
None.

## High-overlap candidates
None at threshold.
