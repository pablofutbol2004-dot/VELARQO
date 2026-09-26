# Database-Reactivation Engine

Ingest messy customer database → clean, segment, score, and export ready for campaigns.

## Use Case

After a client gives you their historical data (lost quotes, no-shows, quotes that expired), clean it and reactivate them with targeted campaigns.

## Input Format (Minimal CSV)

```
name, email, phone, postcode, lead_source, created_at, last_contact, 
quote_value, quote_status, appointment_status, notes, lost_reason
```

Can also accept additional fields (revenue, company size, etc.).

## Processing Pipeline

1. **Normalize** (`lib/normalization`)
   - Standardize names, emails, phone, postcodes
   - Remove duplicates and invalid data
   - Validate basic format

2. **Deduplicate** (`prospecting/deduplication`)
   - Find exact duplicates (email + name)
   - Find fuzzy matches (similar names + postcode)
   - Keep one canonical record
   - Note duplicates for data quality check

3. **Segment** (`lib/segmentation`)
   - Group by outcome: quoted, lost, no-show, expired, etc.
   - Tag by customer lifecycle stage
   - Identify high-value vs. low-value

4. **Score Recoverability** (`lib/scoring`)
   - How likely to convert if reactivated
   - Based on: time since last contact, quote value, reason for loss
   - Higher score = prioritize first

5. **Economic Prioritization** (`database-reactivation/opportunity-scoring`)
   - Calculate recovery value
   - Revenue × likelihood to convert
   - Sort by potential ROI

6. **Loss Analysis** (`database-reactivation/reply-routing`)
   - Categorize reasons for loss (price, timing, competitor, no-show)
   - Predict probable reason if missing
   - Use for campaign personalization

7. **Campaign Recommendation** (`database-reactivation/campaign-generator`)
   - Different angles for different segments
   - Lost → "We've improved pricing"
   - No-show → "Let's reschedule"
   - Expired → "Still interested?"

8. **Personalization** (`lib/personalization`)
   - Reference their history: quote value, lost reason
   - Generate angle specific to why they left
   - Mention value improvements since then

9. **Suppression Lists** (`database-reactivation/segmentation`)
   - Remove: recently contacted, unsubscribed, clearly dead
   - Flag: bad email format, no contact info
   - Export: clean list only

10. **Export** (`integrations/ghl`)
    - Format for GHL import (contact + fields)
    - Create segments for different campaign approaches
    - Generate personalized email copy
    - Ready for immediate sending

## Output Deliverables

1. **Cleaned Lead Database** (CSV)
   - Normalized, deduplicated, validated

2. **Segmented Leads** (CSV files)
   - By segment type (quoted, lost, no-show, etc.)
   - By priority (high, medium, low)

3. **Scored Database** (CSV)
   - Each lead with recoverability score
   - Economic priority score
   - Recommended segment

4. **Campaign Briefs** (JSON/CSV)
   - 1 per segment: angle, offer, copy suggestions
   - Personalization fields to use
   - Expected metrics

5. **GHL Import File** (CSV)
   - Ready to import as contacts
   - Custom fields populated
   - Segmented into different pipelines

6. **Analytics/Tracking Setup**
   - Campaign IDs to track responses
   - Email templates pre-configured
   - Reply webhook ready

## Example Workflow

```
Client Database CSV (500 contacts)
  ↓ normalize (460 valid)
  ↓ deduplicate (430 unique)
  ↓ segment
    ├─ quoted: 120
    ├─ lost: 180
    ├─ no-show: 80
    └─ expired: 50
  ↓ score + prioritize
  ↓ loss analysis
  ↓ create campaigns
  ↓ personalize copy
  ↓ export to GHL
  ↓ send + track + measure
```

## Configuration

Uses ICP template from `config/templates/` but adapts for reactivation:
- Different offer angles for different segments
- Less aggressive (they know you already)
- Focus on what changed since they left
- Emphasize improved solution/pricing/timeline

## Metrics Output

Per campaign:
- Contacts in segment
- Emails sent
- Open rate
- Reply rate
- Positive/maybe/negative split
- Appointments booked
- Quotes requested
- Sales closed
- Revenue recovered
- Cost per acquisition

After 10 clients:
- Segment recovery rates by vertical
- Offer effectiveness by segment
- Typical revenue recovered per customer
- Best timing for reactivation
- Most effective angles

## Database Schema

See `data/schemas/lead.schema.json`

Extended fields:
- `quote_value` - Original quote amount
- `quote_status` - quoted, lost, won, expired
- `appointment_status` - booked, no-show, attended, cancelled
- `lost_reason` - price, timing, competitor, no-show, not-ready
- `recovery_score` - 0-100 likelihood to convert
- `economic_priority` - rank for campaign priority
