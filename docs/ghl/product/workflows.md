# Workflows

Support Portal: https://help.gohighlevel.com/support/solutions/48000455132
Overview article: https://help.gohighlevel.com/support/solutions/articles/155000002288

Triggers, actions, waits, branches, filters, Workflow AI, inbound webhooks.

## Important caveat (do not assume otherwise)

Per `VELARQO_PRIORITY.md` and the note in `docs/ghl/README.md`'s companion
guidance: **the public Workflow API's coverage is not equivalent to the
full UI workflow builder.** Don't assume Velarqo can programmatically
create/edit arbitrary workflow logic via API just because the UI supports
it — check `api/official-docs` for what the Workflow API surface actually
exposes before designing any feature that assumes otherwise, and treat
workflows primarily as something configured once per client (often from a
Snapshot, see `product/snapshots.md`) rather than something Velarqo
generates dynamically per campaign.

## Velarqo's actual use of workflows

Workflows are GHL's execution/orchestration layer for what happens *after*
Velarqo hands off a qualified lead or reactivation campaign — follow-up
sequencing, internal notifications, pipeline stage automation. Complex
scoring, segmentation, and campaign strategy stay in Velarqo
(`lib/scoring`, `lib/segmentation`, `database_reactivation/`) precisely so
that logic isn't trapped inside a specific client's workflow builder
config and remains portable/testable — see `VELARQO_PRIORITY.md`
"Recommended architecture."
