# Rate limits

Canonical: https://marketplace.gohighlevel.com/docs/other/rate-limits/

## Current published limits (public v2/v3 OAuth APIs)

- **Burst**: 100 requests / 10 seconds, per Marketplace app per resource,
  per Location (or Company for agency-level resources).
- **Daily**: 200,000 requests / day, per Marketplace app per resource.

These are per resource type (contacts, opportunities, etc. are counted
separately), not one shared pool across the whole API.

## Design implications for Velarqo integrations

- **Batch where the API allows it** (e.g. bulk contact/tag endpoints) instead
  of one call per record — a 500-lead cold-outreach batch as 500 individual
  `POST /contacts/upsert` calls burns burst budget fast.
- **Backoff on 429**: exponential backoff with jitter, respect any
  `Retry-After` header if present.
- **Queue, don't fire-and-forget**: campaign sends and reactivation exports
  should go through a rate-limited queue (`integrations/ghl/`), not direct
  loop-and-call, since a single client's database-reactivation batch can
  be thousands of records.
- **Multi-tenant math**: limits are per Marketplace app per Location. If
  Velarqo runs one Private Integration Token per client (see `AUTH.md`),
  each client gets their own budget — good. If Velarqo ever centralizes
  under one Marketplace app across many client Locations, the daily limit
  is still per-Location, but burst coordination across concurrent client
  jobs needs its own local rate limiter to avoid cross-client interference
  in shared worker processes.

*Source: user-provided (2026-09-27). Treat as version/plan-sensitive per
`AGENTS_GHL.md` — re-check the live Rate Limits page before production
rollout, and before assuming any specific endpoint follows the general
limit rather than a documented exception.*
