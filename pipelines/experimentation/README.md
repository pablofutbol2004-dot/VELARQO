# Experimentation System

Track every campaign → build proprietary dataset → generate automatic insights.

## Objective

After 10 clients with 5,000+ leads sent across different verticals and segments, you have:
- Segment conversion data
- Message variant performance
- Offer effectiveness rankings
- Optimal timing/day/hour
- Revenue per 100 leads by vertical
- Loss patterns
- Seasonal effects

This dataset becomes a moat: you can predict outcomes before sending.

## What to Track

Every email send creates a record:

```
Company
├─ Basic Info
│  ├─ company_name
│  ├─ vertical (windows, kitchens, solar, etc.)
│  └─ segment (quoted, lost, no-show, etc.)
│
├─ Campaign Config
│  ├─ message_variant (1, 2, 3 = A/B/C)
│  ├─ offer (discount %, free survey, etc.)
│  └─ campaign_id
│
├─ Send Details
│  ├─ send_time
│  ├─ send_day (Monday - Sunday)
│  └─ send_hour
│
└─ Outcomes (tracked over 30 days)
   ├─ Engagement
   │  ├─ opened
   │  ├─ reply
   │  └─ reply_sentiment (positive/maybe/negative)
   │
   ├─ Conversion
   │  ├─ appointment_booked
   │  ├─ quote_requested
   │  └─ quote_value
   │
   └─ Revenue
      ├─ sale_closed
      └─ revenue
```

## Data Collection Points

### Send Time (Step 1: Cold Outreach Pipeline)
```
INSERT experiment_result (
  campaign_id, lead_id, company_name, vertical, segment,
  message_variant, offer, send_time, send_day, send_hour,
  opened=false, reply=false, ...other=null
)
```

### Reply Received (Step 10: Reply Webhook)
```
UPDATE experiment_result SET reply=true, reply_text=..., updated_at=NOW()
```

### Reply Classified (Step 11: Reply Classifier)
```
UPDATE experiment_result SET reply_sentiment='positive', updated_at=NOW()
```

### Appointment Booked (Step 13: Route to Sequence)
```
UPDATE experiment_result SET appointment_booked=true, updated_at=NOW()
```

### Sale Synced from GHL (Integration)
```
UPDATE experiment_result SET 
  sale_closed=true, 
  revenue=..., 
  updated_at=NOW()
```

## Analysis Queries (Auto-Generate)

### 1. Message Variant Performance
```
SELECT 
  message_variant,
  COUNT(*) as emails_sent,
  SUM(CASE WHEN reply THEN 1 ELSE 0 END) / COUNT(*) as reply_rate,
  SUM(CASE WHEN appointment_booked THEN 1 ELSE 0 END) / COUNT(*) as appointment_rate,
  SUM(revenue) as total_revenue,
  SUM(revenue) / COUNT(*) as revenue_per_email
FROM experiment_result
GROUP BY message_variant
ORDER BY revenue_per_email DESC
```

### 2. Segment Effectiveness
```
SELECT 
  segment,
  COUNT(*) as total,
  SUM(CASE WHEN reply THEN 1 END) / COUNT(*) as reply_pct,
  SUM(CASE WHEN sale_closed THEN 1 END) / COUNT(*) as close_rate,
  SUM(revenue) / COUNT(*) / 100 as revenue_per_100
FROM experiment_result
GROUP BY segment
```

### 3. Optimal Send Times
```
SELECT 
  send_day, send_hour,
  COUNT(*) as emails_sent,
  SUM(CASE WHEN reply THEN 1 END) / COUNT(*) as reply_rate,
  SUM(revenue) / COUNT(*) / 100 as revenue_per_100
FROM experiment_result
GROUP BY send_day, send_hour
ORDER BY revenue_per_100 DESC
```

### 4. Offer Performance
```
SELECT 
  offer,
  COUNT(*) as total,
  SUM(CASE WHEN appointment_booked THEN 1 END) / COUNT(*) as appointment_rate,
  SUM(revenue) / COUNT(*) / 100 as revenue_per_100
FROM experiment_result
GROUP BY offer
```

### 5. Vertical Insights
```
SELECT 
  vertical,
  COUNT(*) as emails_sent,
  SUM(CASE WHEN reply THEN 1 END) / COUNT(*) as reply_rate,
  SUM(CASE WHEN sale_closed THEN 1 END) / COUNT(*) as close_rate,
  AVG(quote_value) as avg_quote,
  SUM(revenue) / COUNT(*) as revenue_per_email
FROM experiment_result
GROUP BY vertical
```

## Dashboard Metrics (Auto-Update)

### Campaign Summary
- Emails sent this week/month
- Reply rate (overall + by segment)
- Appointment booking rate
- Close rate
- Revenue generated

### Performance by Dimension
- Message variant rankings
- Segment effectiveness table
- Best/worst send times
- Offer performance comparison
- Vertical benchmarks

### Cohort Analysis
- New clients vs. repeat
- First campaign vs. reactivation
- By company size
- By lead source

### Forecasting
- Expected appointments (based on reply rate)
- Expected revenue (based on close rate)
- Campaign efficiency ($/lead to revenue)

## Insights Generation (Quarterly)

After each 10-client batch:

1. **Message Insights**
   - "Variant B outperforms by 23%"
   - "Best opening line for segment X is Y"

2. **Segment Insights**
   - "Lost quotes convert at 2x rate of no-shows"
   - "Quoted segment needs 60-day timeout before reactivation"

3. **Timing Insights**
   - "Tuesday 9am gets 15% more replies"
   - "Weekend sends have 3x lower reply rate"

4. **Vertical Insights**
   - "Windows vertical close at 32%"
   - "Kitchen vertical needs lower initial ask"

5. **Offer Insights**
   - "Free survey beats discount offer in reactivation"
   - "Urgency (48-hour) adds 8% to reply rate"

6. **Economic Insights**
   - "£500+ quotes need 2-3 more touches"
   - "First-time leads need longer sequence (7 → 9)"

## Database Schema

See `data/schemas/experiment.schema.json`

## Storage

- **Active**: Last 90 days in operational database
- **Archive**: Older data in data warehouse
- **Indexes**: (campaign_id, message_variant), (segment, reply_sentiment), (send_day, send_hour)

## Tech Requirements

- Database with timestamp precision (PostgreSQL, MongoDB)
- Time series analysis capability
- Automated query scheduler (runs insights monthly)
- Dashboard renderer (JSON → charts)

## Expected Data After 10 Clients

```
Clients: 10
Verticals: Windows, Kitchens, Solar
Leads Sent: 5,000
Replies: 400 (8%)
Appointments: 65 (1.3% of replies)
Sales Closed: 20 (30% of appointments)
Total Revenue: £150,000
Campaign Cost: £2,000 (email + enrichment)

Moat Value:
- Know which message variant works for kitchens
- Know optimal timing for reactivation
- Know which segments respond best
- Predictive model for quote-to-sale conversion
- This data is worth $$$ - either to sell services or build as SaaS
```
