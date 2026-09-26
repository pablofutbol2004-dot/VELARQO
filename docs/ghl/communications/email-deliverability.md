# Email deliverability

Support Portal: https://help.gohighlevel.com/support/solutions/articles/48001213941

For Velarqo this matters more than most raw GHL API coverage — a cold
outreach or reactivation campaign with a warm ICP fit and good copy still
fails if the sending domain is unwarmed or misconfigured.

## Before sending any real campaign

- **Warm up the sending domain/account** gradually — don't blast a fresh
  domain with the full cold-outreach batch on day one. Ramp volume.
- **Dedicated sending domain per client**, not a shared Velarqo domain, so
  one client's poor list hygiene can't tank another client's deliverability.
- **SPF/DKIM/DMARC configured** on the sending domain before the first send.
  See `email-domains.md`.
- **List hygiene first**: this is exactly what `prospecting/deduplication`
  and `client_onboarding/data_quality` already do (invalid email detection,
  dedup) — deliverability is a reason those steps are mandatory, not optional
  cleanup.

## Ongoing

- Monitor bounce/complaint rates per client/domain; a spike should pause
  that client's sends, not just log a warning.
- Suppression lists (`database_reactivation/segmentation/suppression.py`)
  double as deliverability protection, not just a courtesy — repeatedly
  emailing unengaged contacts damages sender reputation.
