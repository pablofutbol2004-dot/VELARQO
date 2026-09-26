# Authentication

Canonical: https://marketplace.gohighlevel.com/docs/Authorization/OAuth2.0/
Scopes: https://marketplace.gohighlevel.com/docs/Authorization/Scopes/

## Two patterns

- **Private Integration Token** — best fit for Velarqo's internal/single-account
  tooling (one client's own sub-account). No OAuth dance, simpler to operate.
- **OAuth 2.0 Authorization Code flow** — required for Marketplace/public apps
  or delegated multi-account access (needed if Velarqo ever manages many
  client sub-accounts from one app installation).

Default for Velarqo: Private Integration Token per client, unless/until we
manage many client accounts from a single Marketplace app — re-evaluate at
that point rather than defaulting to OAuth complexity early.

## Token lifetimes (OAuth path)

- Access token: valid 1 day.
- Refresh token: rotates on use, can remain valid up to ~1 year.

Design implication: any OAuth-based integration must refresh proactively
(don't wait for a 401) and persist the rotated refresh token immediately —
losing a rotated refresh token breaks the connection until re-auth.

## Scopes

Request the minimum scope set for the endpoints actually used (e.g.
`contacts.write`, `opportunities.readonly`). Check `docs/ghl/api/official-docs`
for the scope required per endpoint — it's listed per-operation in the
OpenAPI `security` block, not just in the general scopes page.

*Source: user-provided (2026-09-27), consistent with the Developer Portal
pages linked above. Re-verify against the live Developer Portal before
building production auth — this is exactly the kind of detail that drifts.*
