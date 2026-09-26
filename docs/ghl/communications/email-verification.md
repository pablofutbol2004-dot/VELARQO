# Email verification

Support Portal (Email section): https://help.gohighlevel.com/support/solutions/48000449563

Verify email addresses (catch typos, dead domains, role accounts) before
they enter a send queue — bounces hurt deliverability for every future send
from that domain, not just the one bad address.

## Where this belongs in the existing pipeline

`lib/normalization/normalize.py::normalize_email()` currently only checks
*format* (regex), not deliverability (does the mailbox/domain actually
exist). That's a real gap once real sending is wired up:

- Format-invalid emails are already correctly dropped (see
  `test_pipeline_rejects_invalid_email`).
- Format-valid-but-undeliverable emails (typos like `gmial.com`, dead
  domains, full mailboxes) currently pass through untouched.

Before connecting a real email provider, add a verification step (either
the provider's own verification API, or a dedicated verification service)
between `normalize_lead()` and `enrich_lead()` in
`pipelines/cold_outreach/pipeline.py`, and a matching step in
`pipelines/database_reactivation/pipeline.py` before suppression — a
verified-bad email should suppress a reactivation record, not just get
sent and bounce.
