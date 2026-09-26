# Snapshots

Support Portal (Agency admin): part of https://help.gohighlevel.com/support/solutions/155000000204

A Snapshot is GHL's mechanism for cloning a pre-built sub-account
configuration (pipelines, workflows, custom fields, calendars) into a new
client's Location. Tier 2 per `VELARQO_PRIORITY.md`.

## Why this matters for Velarqo specifically

`client_onboarding/` (intake, field mapping, data quality) currently
handles the *data* side of onboarding a new client — mapping their messy
CSV export onto Velarqo's schema. Snapshots are the *GHL-side* equivalent:
provisioning a new client's Location with the right custom fields
(matching `product/contacts.md`'s field mapping table), pipeline stages
matching Velarqo's segment model (`lost`/`no_show`/`expired`/`quoted`/`won`),
and any standard workflows.

Building a Velarqo-standard Snapshot (once the custom field/pipeline
mapping is finalized) turns "set up a new client in GHL" into "apply
snapshot + run `client_onboarding` intake," rather than manual per-client
GHL configuration each time. Not built yet — this is a setup task, not
code, but worth doing before the second or third client rather than
after.
