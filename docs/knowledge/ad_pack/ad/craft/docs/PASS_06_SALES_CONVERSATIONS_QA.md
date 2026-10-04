# Pass 06 — Sales Conversations QA

## Structural
- Sales-conversation rules: **45**
- Categories: **9**
- Library packs after pass: **18**
- Library rules after pass: **418**
- Existing rules migrated out: **0**

## Corpus provenance
- Broad candidate routing: **5,246 / 11,917 transcripts**
- C12K references in new pack: **90**
- Unique C12K anchors in new pack: **74**
- Unique source transcripts represented: **10**
- Missing transcript files/timestamps: **0**

## Duplication
- Exact cross-pack duplicate rules: **0**
- High-overlap cross-pack candidates at QA threshold: **0**

## Boundary / scope QA
- `sales_conversations` owns interactive framing, diagnosis, listening/question execution, recommendation, objection clarification, proof timing in dialogue, decision/close, follow-up continuity, and call-review practice.
- Qualification criteria, scoring, authority/budget/timing gates, and routing definitions remain in `qualification`.
- Price/terms, concessions, guarantees, payment structures, and scarcity remain in `offer_framing`.
- Funnel nurture/re-entry state machines and channel handoffs remain in `funnel_mechanics`.
- Claim → doubt → evidence selection remains in `proof`; this pack only covers how chosen evidence is integrated into dialogue.

## Benchmark / volatility QA
- Exact close rates, call lengths, one-call/two-call price thresholds, follow-up counts, and same-day-decision targets were treated as contextual examples rather than timeless benchmarks.
- Named scripts/frameworks were decomposed into mechanisms instead of preserved as universal doctrine.

## Source failures
None.

## High-overlap candidates
None at threshold.
