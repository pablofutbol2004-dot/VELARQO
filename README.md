# Business Platform

Niche-agnostic intelligence engine for B2B outreach, lead management, and revenue recovery.

## Core Systems

1. **Cold Outreach Pipeline** - CSV → normalize → deduplicate → enrich → qualify → personalize → send → classify
2. **Database-Reactivation Engine** - Ingest messy customer data → clean → segment → score → export → track results
3. **Experimentation System** - Track all campaign metrics → build proprietary dataset and insights

## Architecture

Velarqo's own outreach (acquiring clients) and a signed client's execution
layer (running their business) are two different systems using two
different channels — don't conflate them:

```
Velarqo's own cold outreach (acquiring clients):
CSV Input → Prospecting Pipeline → Outreach Pipeline → Reply Tracking → Analytics
                                         ↓
                              Google Workspace / Outlook
                              (integrations/email/ - Velarqo's own mailbox)
                                         ↓
                                    Appointments & Sales

A signed client's fulfillment (running their business, later):
                                  GHL Integration
                          (client's CRM, communication, execution)
```

GHL is not the send channel for Velarqo's own prospecting — it's reserved
for client fulfillment once a client signs up. See
`docs/ghl/VELARQO_PRIORITY.md` and `docs/ghl/GHL_FOR_VELARQO.md`.

## Modules

### Pipelines (Orchestration)
- `cold-outreach/` - Email campaign workflow
- `database-reactivation/` - Customer recovery engine
- `experimentation/` - Metrics and insights

### Data Layer
- `data/models/` - Data definitions
- `data/schemas/` - JSON schemas for all entities
- `data/migrations/` - Schema versions

### Shared Libraries
- `lib/enrichment/` - Data enrichment (LinkedIn, email, company)
- `lib/normalization/` - Data standardization
- `lib/scoring/` - ICP fit, lead quality, priority
- `lib/segmentation/` - Customer grouping
- `lib/personalization/` - Copy generation
- `lib/ai/` - AI integrations (prompts, models)
- `lib/tracking/` - Campaign and experiment tracking

### Integration Layer
- `integrations/email/` - Velarqo's own outreach send channel: Gmail API (Google Workspace) and Outlook (Microsoft Graph)
- `integrations/ghl/` - GoHighLevel sync, for client fulfillment (not Velarqo's own outreach)
- `integrations/sms/` - SMS provider
- `integrations/google_sheets/` - Data import/export
- `integrations/webhooks/` - Reply tracking

### Configuration
- `config/templates/` - ICP and workflow templates
- `config/workflows/` - Workflow definitions
- `config/prompts/` - AI prompt templates

### Testing
- `tests/fixtures/` - Sample data
- `tests/integration/` - End-to-end tests

### Documentation
- `docs/architecture/` - System design
- `docs/workflows/` - Process flows
- `docs/api/` - API reference

## Key Design Principles

1. **Niche Agnostic** - Change ICP template, prompts, and data → runs for windows, kitchens, solar, roofing, etc.
2. **Synthetic Data Ready** - Build and test against fake CSV before real campaigns
3. **Two separate execution layers** - Velarqo's own outreach sends via Google Workspace/Outlook; GHL is the client's execution layer once they sign up
4. **Metrics First** - Every email tracked for experimentation
5. **Proprietary Moat** - After 10 clients, dataset becomes competitive advantage

## Quick Start

1. Configure ICP in `config/templates/`
2. Prepare CSV (or use synthetic test data)
3. Run prospecting pipeline
4. Review qualified leads
5. Generate personalized emails
6. Send via email integration
7. Track replies and conversions
8. Analyze results

## Tech Stack

(To be defined - Python/Node.js/etc.)
