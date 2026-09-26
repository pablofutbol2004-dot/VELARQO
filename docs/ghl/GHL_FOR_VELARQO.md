# GHL for Velarqo

Not documentation of GHL itself — a translation layer between Velarqo's
concepts (this repo's code) and GHL's implementation of them. Read this
before `product/*.md` or the raw API docs when the question is "how does
*our* thing map onto GHL," not "what does GHL support."

## Concept map

| Velarqo concept | Velarqo code | GHL implementation |
|---|---|---|
| Client | — (per-deployment config) | Sub-account / Location |
| Prospect | `lead` (`data/schemas/lead.schema.json`) | Contact |
| Qualified lead | `lead.qualified`, `lead.icp_score` | Contact + custom fields/tags |
| Historical customer record | `reactivation_record` (`data/schemas/reactivation_record.schema.json`) | Contact + custom fields |
| Sales opportunity | — (not modeled yet) | Opportunity |
| Pipeline stage | `reactivation_record.segment` / `experiment_result.segment` | Opportunity stage |
| Recovered DB lead | `reactivation_record` post-campaign | Contact + campaign/workflow state |
| Appointment | `experiment_result.appointment_booked/date` | Calendar event |
| SMS/email conversation | `outreach/reply_classifier`, `integrations/webhooks` | Conversation |
| Campaign automation | `outreach/campaign_builder`, `database_reactivation/campaign_generator` | Workflow |
| Client onboarding | `client_onboarding/` (intake, field_mapping, data_quality) | Snapshot + API provisioning |
| Campaign configuration | `config/templates/icp-template.json` | Custom fields + workflows |
| ICP scoring / lead scoring | `lib/scoring` | — (Velarqo, outside GHL) |
| Segmentation | `lib/segmentation`, `database_reactivation/segmentation` | — (Velarqo, outside GHL) |
| Campaign strategy generation | `lib/ai/research`, `database_reactivation/campaign_generator` | — (Velarqo, outside GHL) |
| Execution (send, book, notify) | — | GHL |
| Event stream | — (not built yet) | GHL webhooks → Velarqo (see `api/WEBHOOKS.md`) |
| Analytics / experimentation | `lib/tracking/insights.py`, `experiment_result` table | GHL data feeds in → Velarqo DB is source of truth |

## What this means concretely, right now

1. **No `integrations/ghl/` client exists yet beyond `integrations/ghl/export.py`**
   (a one-way CSV export for the database-reactivation pipeline). There is
   no live API client, no webhook receiver wired to a real endpoint, and no
   OAuth/token handling. Everything in `api/`, `product/`, and
   `communications/` here is preparation for building that, grounded in the
   vendored official docs (`api/official-docs/`) — not a description of
   something already built.

2. **The three core systems (`pipelines/cold_outreach`, `pipelines/database_reactivation`,
   `pipelines/experimentation`) are GHL-agnostic by design** — see
   `VELARQO_PRIORITY.md`'s "Recommended architecture." Building the GHL
   integration means adding an `integrations/ghl/client.py` (auth + upsert
   calls per `product/contacts.md` / `product/opportunities.md`) and
   webhook handlers (per `api/WEBHOOKS.md`) that call the *existing*
   pipeline functions — not rewriting the pipelines to know about GHL
   internals.

3. **The natural seam points**, by file:
   - `lib/tracking/experiments.py` — add GHL-sourced writers
     (`record_appointment`/`record_sale` triggered by webhooks, not just
     called from the CLI).
   - `integrations/ghl/export.py` — replace/extend the CSV export with a
     real `POST /contacts/upsert` call once a Private Integration Token
     exists for a client (see `api/AUTH.md`).
   - `integrations/webhooks/reply_webhook.py` — add a GHL conversation
     variant alongside the current generic one.

4. **Multi-client from day one in the data model, even single-client in
   deployment**: `lead.ghl_contact_id` already exists in the schema
   precisely so the upsert-then-store-id pattern (`AGENTS_GHL.md`'s
   idempotency rule) has somewhere to go once wired up.
