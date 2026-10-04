# Deployment blueprint

## Minimum architecture

- **Supabase/Postgres**: canonical database, audit evidence, RLS/admin access.
- **VPS worker service**: schedulers, enrichment adapters, queue workers, reply ingest, analysis jobs.
- **Secrets manager / environment**: provider API credentials; never store API keys in tables/logs.
- **Google Workspace or equivalent mailboxes**: sending identities, governed separately by outbound-readiness controls.
- **LLM API**: optional classification/drafting layer; never authoritative for compliance, identity or suppression.

## Suggested services

`api/` internal admin API
`workers/` background jobs
`adapters/` provider integrations
`policy/` qualification/compliance/queue rules
`analytics/` funnel + experiment metrics
`admin/` human-review screens or CLI

## Observability

Alert on:
- queue retries / duplicate idempotency attempts
- hard bounce increase
- provider failure rate
- suppression/complaint event
- send while campaign paused attempt
- entity/compliance-review backlog
- verifier unknown/accept-all spike
- reply-ingest lag

## Scale rule

Do not increase daily send volume until data-quality and reply-processing capacity remain healthy. Acquisition throughput is constrained by the slowest reliable stage, not mailbox theoretical capacity.
