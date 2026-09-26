# Business Platform

Niche-agnostic intelligence engine for B2B outreach, lead management, and revenue recovery.

## Core Systems

1. **Cold Outreach Pipeline** - CSV → normalize → deduplicate → enrich → qualify → personalize → send → classify
2. **Database-Reactivation Engine** - Ingest messy customer data → clean → segment → score → export → track results
3. **Experimentation System** - Track all campaign metrics → build proprietary dataset and insights

## Architecture

```
CSV Input → Prospecting Pipeline → Outreach Pipeline → Reply Tracking → Analytics
                                         ↓
                                  GHL Integration
                                  (CRM, communication, execution)
                                         ↓
                                    Appointments & Sales
```

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
- `integrations/ghl/` - GoHighLevel sync
- `integrations/email/` - Email provider (SendGrid, etc.)
- `integrations/sms/` - SMS provider
- `integrations/google-sheets/` - Data import/export
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
3. **GHL Complementary** - We handle intelligence; GHL handles execution
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
