# API changelog

Canonical: https://marketplace.gohighlevel.com/docs/Changelog/

HighLevel's API changes actively — endpoints get added/removed and request
schemas change (e.g. the ongoing v1 -> v2/v3 migration, v1 end-of-support
2025-12-31). Treat the changelog as a first-class source to check, not an
afterthought, specifically:

- **Before implementing** any new endpoint integration — confirm the DTO
  shape in `api/official-docs` matches what the changelog says is current,
  since the local vendored repo is synced periodically, not continuously.
- **Before upgrading** the `api/sdk` version pin — read what changed between
  the pinned version and the target version.
- **When a previously-working integration starts failing** — check here
  before assuming the bug is in Velarqo's code.

This file is intentionally just a pointer, not a mirror — see
`docs/ghl/README.md` ("Why the Support Portal is not copied wholesale")
for why: a stale local copy of a changelog is actively misleading.

## Related

- Product changelog (UI/feature changes, separate from the API):
  `docs/ghl/sources/PRODUCT_CHANGELOG.md`
