# Business Platform Architecture

## High-Level Flow

```
        ┌─────────────────────────────────────────────────┐
        │           EXTERNAL DATA SOURCES                  │
        │  CSV, CRM Export, LinkedIn, Email Enrichment     │
        └──────────────────┬──────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────────────┐
        │         PROSPECTING PIPELINE                     │
        │  ├─ Normalize                                    │
        │  ├─ Deduplicate                                  │
        │  ├─ Enrich (LinkedIn, email finder)             │
        │  ├─ Qualify (Company size, industry)            │
        │  └─ Score ICP (0-100)                           │
        └──────────────────┬──────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────────────┐
        │         OUTREACH PIPELINE                        │
        │  ├─ Research (Generate company summary)          │
        │  ├─ Angle (Personalized hook)                    │
        │  ├─ Personalize (Email copy)                     │
        │  ├─ Campaign Queue (Batch + timing)              │
        │  └─ Send (Email provider)                        │
        └──────────────────┬──────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────────────┐
        │        EMAIL PROVIDER (SendGrid, etc.)           │
        │  └─ Webhook callback for replies                 │
        └──────────────────┬──────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────────────┐
        │        REPLY PROCESSING PIPELINE                 │
        │  ├─ Webhook capture                              │
        │  ├─ Classification (AI: positive/maybe/negative) │
        │  ├─ Route (Sequence vs. stop)                    │
        │  └─ Sync to GHL (Positive leads)                │
        └──────────────────┬──────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────────────┐
        │         GODHIGHLEVEL (Execution)                 │
        │  ├─ CRM (Contact + deal data)                    │
        │  ├─ Calendar (Appointment scheduling)            │
        │  ├─ Automation (Follow-up sequences)             │
        │  ├─ Communications (SMS, calls)                  │
        │  └─ Pipelines (Sales process)                    │
        └──────────────────┬──────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────────────┐
        │         EXPERIMENTATION SYSTEM                   │
        │  ├─ Track (Every send + outcome)                 │
        │  ├─ Analyze (Message variant, timing, segment)  │
        │  ├─ Insights (Auto-generate dashboards)          │
        │  └─ Predict (Model future performance)           │
        └─────────────────────────────────────────────────┘
```

## Core Responsibility Boundaries

| Component | Responsibility |
|-----------|-----------------|
| **business-platform** | Intelligence: normalize, enrich, qualify, score, personalize, track |
| **GoHighLevel** | Execution: CRM, scheduling, communication, pipeline management |

## Three Core Systems

### 1. Cold Outreach Pipeline
**Goal**: CSV → 8 appointments per 100 leads

- Normalize and enrich lead data
- Score fit to ICP
- Generate personalized angles
- Send emails with A/B variants
- Track replies and conversions
- Route positives to GHL

**Niche Agnostic**: Configuration only (swap ICP, vertical keywords, prompts)

### 2. Database-Reactivation Engine
**Goal**: Old customer database → £10k+ recovered revenue per 100 records

- Import messy historical data
- Clean, deduplicate, validate
- Segment by outcome (lost, no-show, quoted, etc.)
- Score recovery probability
- Generate segment-specific campaigns
- Export ready for GHL

**Niche Agnostic**: Different segments for different verticals

### 3. Experimentation System
**Goal**: After 10 clients, own proprietary performance dataset

- Track every email: send time, variant, offer, segment
- Measure outcomes: reply, appointment, sale, revenue
- Auto-generate insights by dimension
- Build predictive models
- Create competitive moat

## Data Flow

### Example: Cold Outreach (Windows Client)

```
Windows Company CSV (500 companies)
    ↓ [Normalize]
  480 valid records
    ↓ [Deduplicate]
  450 unique
    ↓ [Enrich]
  Fetch LinkedIn data, email, company info
    ↓ [Qualify]
  Check: company size 20-200, UK, industry match
    ↓ [Score ICP]
  310 companies scoring 65+
    ↓ [Research & Angle]
  Generate research, personalized hook
    ↓ [Personalize Email]
  3 variants (A/B/C) of copy
    ↓ [Campaign Queue]
  Send on optimal days/times
    ↓ [Reply Tracking]
  Monitor for 21 days
    ↓ [Classification]
  Positive: 25 (8%), Maybe: 10 (3%), Negative: 5 (1.6%)
    ↓ [Sync to GHL]
  25 leads → pipeline → sales team
    ↓ [Results]
  8 appointments scheduled (2.6% of sent)
  2 quotes requested (0.6%)
  1 sale closed (0.3%)
  Revenue: £3,500

Experiment data collected:
  - Message variant C performed 15% better
  - Tuesday 9am had 12% better reply rate
  - Companies 50-100 employees close at 40%
```

### Example: Database Reactivation (Kitchen Client)

```
Kitchen Database Export (1,200 historical contacts)
    ↓ [Normalize & Deduplicate]
  950 unique
    ↓ [Segment]
  - Quoted: 320
  - Lost: 480
  - No-show: 150
    ↓ [Score Recoverability]
  - High priority (lost < 6 months): 180
  - Medium priority (6-12 months): 240
  - Low priority (> 12 months): 530
    ↓ [Loss Analysis]
  - Price was issue: 200
  - Timing (not ready): 150
  - Chose competitor: 130
    ↓ [Campaign Recommendations]
  - Price segment → new pricing offer
  - Timing segment → "ready now?"
  - Competitor segment → feature comparison
    ↓ [Personalization]
  Generate 3 different email angles
    ↓ [Export to GHL]
  - High priority: 180 → campaign A
  - Medium priority: 240 → campaign B
    ↓ [Results]
  - 24 replied (2%)
  - 6 appointments (0.5%)
  - 2 sales (0.17%)
  - Revenue recovered: £8,400

Experimentation:
  - Lost segment converts at 2x vs. no-show
  - Price offer beats urgency offer
  - Time decay: best within 6 months
```

## Dependencies & Integrations

### Required APIs/Services
- Email provider (SendGrid, Mailgun)
- Email finder (Hunter.io, RocketReach)
- GoHighLevel API
- LinkedIn API (optional but recommended)

### Optional Enhancements
- Clearbit (company data)
- Apollo (B2B database)
- Slack notifications
- Zapier/Make for workflows

### Data Storage
- PostgreSQL (operational data, experiments)
- S3 or GCS (backup, archive)

## Configuration-First Design

Everything configurable in `config/`:

```
config/templates/icp-template.json
├─ vertical (windows, kitchens, solar, etc.)
├─ company_size, revenue range
├─ industry keywords
├─ qualification threshold
├─ email variants
├─ optimal send times
└─ expected metrics

config/workflows/
├─ cold-outreach-sequence.json
├─ reactivation-campaign-lost.json
└─ reactivation-campaign-no-show.json

config/prompts/
├─ research-prompt.txt
├─ angle-prompt.txt
├─ email-personalization-prompt.txt
└─ reply-classification-prompt.txt
```

Change `windows` → `kitchens` by:
1. Update `icp-template.json` (keywords, size, revenue)
2. Update prompts (kitchen-specific angles)
3. Use same pipeline code

## Scaling Model

### Phase 1 (Months 1-3): Windows UK
- Build complete cold outreach pipeline
- Test database reactivation engine
- Track first 500 experiment results

### Phase 2 (Months 3-6): Second Vertical
- Add kitchens or solar
- Reuse all code, change config
- Accumulate 2,000+ experiment records

### Phase 3 (Months 6-9): Third Vertical
- Add roofing, landscaping, or another
- Cross-vertical insights emerge
- 5,000+ experiment records = proprietary dataset

### Phase 4 (Months 9+): Moat & Scale
- Sell as white-label (your platform for other agencies)
- Or build SaaS (subscription for SMBs)
- Or focus on implementation (agency services)

## Competitive Advantages

By January (Phase 1):
✓ Niche-agnostic platform
✓ Works without manual CRM configuration
✓ 8% reply rate on cold outreach (above average)
✓ Database reactivation revenue recovery

By Q2 (Phase 2):
✓ Proprietary data on windows + kitchens
✓ Predictive models for segment performance
✓ 25% appointment conversion on reactivation
✓ Can confidently quote: "£X revenue per client"

By Q3+ (Phase 3-4):
✓ Proprietary dataset across 3+ verticals
✓ Trained models (message variant, segment, timing)
✓ 10x competitive advantage over manual GHL setup
✓ Defensible moat: data + models + workflows

## Success Metrics

**Q4 2025** (By Jan):
- Platform built and tested against synthetic data
- 1 real client cold outreach campaign running
- Basic experimentation tracking live

**Q1 2026** (Jan-Mar):
- First 2 clients, 1,000+ leads processed
- Database reactivation generating £5k+ revenue/client
- Initial insights emerging (best variants, timing)

**Q2 2026** (Apr-Jun):
- 5 clients across 2-3 verticals
- 2,500+ experiment records
- Confidently predictive on segment performance

**Q3 2026** (Jul-Sep):
- 10 clients, 5,000+ records
- Proprietary dataset complete
- Moat defensible, ready to scale/sell
