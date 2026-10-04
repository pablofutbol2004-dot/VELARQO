# Pass 14 — Distribution Through People changelog

## Added

- New library area `kleos/distribution/` (kind `distribution`), registered in the craft loader.
- `kleos/distribution/distribution_through_people/essentials.yaml` — 40 rules across 8 categories.
- `DISTRIBUTION_THROUGH_PEOPLE_REFERENCE.md`, `DISTRIBUTION_REFERENCE.md`.
- Pass 14 QA and roadmap/manifest updates.

## Boundaries enforced

- Kept downstream funnel and sales mechanics in business-mechanics packs.
- Kept generic persuasive/craft principles in their existing homes.
- Deferred high-volatility platform/referral-tool operations to `channel_ops`.

## Migrations

- No existing canonical rules required migration in this pass; semantic duplicate QA found no cross-pack ownership collision at the configured threshold.

## Wiring note

`distribution_through_people` is not part of any draft/format bundle. It will be consumed when the Distribution gear (gear 7) is built; until then it is a validated, referenced library pack.
