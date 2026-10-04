# Pass 01 — Proof — changelog

## Added

- `kleos/craft/proof/essentials.yaml` — 28 format-neutral proof rules in 7 categories.
- `PROOF_REFERENCE.md` — extraction method, conflicts, migrations, boundaries, source anchors, and re-check items.

## Migrated / refactored

- `value_communication`: 16 → 15 rules; generic proof-selection rule moved to `proof`; category renamed to `examples_and_comparison`.
- `visual_communication`: 15 → 14; generic visible-proof rule moved to `proof`; category renamed to `comparison_and_demonstration`.
- `cta_conversion`: 14 → 11; generic trust/proof hierarchy rules moved to `proof`.
- `hooks`: 18 → 17; evidence-burden rule moved to `proof`.
- `content_quality`: 17 → 16; claim/evidence matching rule moved to `proof`; integrity/verification remain.
- `packaging`: 12 unchanged; one rule reworded to own expectation/payoff rather than duplicate proof burden.
- `GENERAL_CRAFT_REFERENCE.md`: updated from 12 to 13 current packs and regenerated boundaries/counts for Pass 1.

## Corpus routing

- Full corpus: 11,917 transcripts.
- Broad proof-related routing candidates: ~3,925.
- Candidate count is not an evidence count; high-signal passages were inspected and semantically distilled.

## Roadmap change

- `podcast/clip` is removed entirely. It is not a planned pack.
- `ideation_angles` remains the next general-craft pass.
