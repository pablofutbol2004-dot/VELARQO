# Agent instructions — HighLevel / GoHighLevel

When implementing anything that touches HighLevel:

- Read `GHL_FOR_VELARQO.md` and `VELARQO_PRIORITY.md` first — they say how Velarqo intends to use GHL, which matters more day-to-day than the raw API surface.
- Read `api/API_MAP.md` next for the API surface itself.
- Treat `api/official-docs/` (OpenAPI/JSON/Markdown) as the primary local API source.
- Check `api/CHANGELOG.md` and `sources/PRODUCT_CHANGELOG.md` before trusting anything here as current — this pack is synced/written at a point in time, GHL ships continuously.
- Never invent an endpoint, scope, webhook, field, trigger, workflow action, plan entitlement, or rate limit.
- Prefer private integrations for Velarqo-internal/single-account tooling unless OAuth/Marketplace distribution is actually required.
- Treat workflows as GHL execution/orchestration, not as the only place for Velarqo intelligence. Keep complex scoring, enrichment, segmentation, experimentation, analytics, and reusable business logic outside GHL when that improves portability/testability.
- Build idempotently: upsert contacts where appropriate, store GHL IDs, deduplicate events, verify webhook signatures/auth, and make retries safe.
- Respect DND/consent/compliance state and do not create outbound automations that bypass it. See `communications/` for email/SMS-specific compliance rules (deliverability, verification, SMS opt-outs, A2P).
- For every integration, document: scopes, endpoints, webhook events, custom fields, pipeline stages, retry strategy, rate-limit handling, failure modes, and test fixtures.
- Design around real limits from day one: `api/RATE_LIMITS.md` (burst/daily) and `api/AUTH.md` (token lifetimes) — don't discover these in production.
- If docs disagree, prefer the newest official Developer Portal page for the exact API version being used.
