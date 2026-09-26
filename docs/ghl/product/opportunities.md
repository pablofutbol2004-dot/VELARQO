# Opportunities / pipelines

Support Portal: https://help.gohighlevel.com/support/solutions/articles/155000005062
API surface: `api/official-docs/apps/v3/opportunities-v3.json`

## Key endpoints (v3)

- `POST /opportunities/upsert` — same idempotent pattern as contacts; use
  this from `integrations/ghl/`, not create+update.
- `POST /opportunities/search`
- `GET /opportunities/pipelines` — list pipeline/stage config (fetch and
  cache per client during onboarding, don't hardcode stage names/ids).
- `GET /opportunities/lost-reason` — **GHL has native lost-reason tracking.**
  This is directly equivalent to `reactivation_record.lost_reason`
  (`data/schemas/reactivation_record.schema.json`) — when an opportunity is
  marked lost in GHL with a reason, that should flow back into Velarqo's
  `lost_reason` field via the `OpportunityStatusUpdate` webhook rather than
  Velarqo maintaining a disconnected guess.
- `PUT /opportunities/{id}/status`
- `/opportunities/{id}/followers`

## Mapping onto Velarqo's schema

| Velarqo concept | GHL field/mechanism |
|---|---|
| `experiment_result.segment` (lost/no_show/expired/quoted/won) | Opportunity `status` + pipeline stage |
| `reactivation_record.lost_reason` | Opportunity lost-reason (native) |
| `reactivation_record.quote_value` / `experiment_result.quote_value` | Opportunity `monetaryValue` |
| `experiment_result.appointment_booked` | Calendar event tied to the opportunity/contact (see `product/calendars.md`) |
| `experiment_result.sale_closed`, `revenue` | Opportunity `status = won` + `monetaryValue`, or Invoice/Order events if Velarqo bills through GHL |

## Webhook-driven updates

`OpportunityStageUpdate`, `OpportunityStatusUpdate`,
`OpportunityMonetaryValueUpdate` should call
`lib/tracking/experiments.py::record_appointment` /
`record_sale` on the matching `experiment_result` row (matched by
`lead_id`/`ghl_contact_id`, not by re-deriving state client-side) — see
`api/WEBHOOKS.md` for the general event-handling rules.
