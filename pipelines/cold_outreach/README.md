# Cold Outreach Pipeline

End-to-end workflow: CSV → normalize → deduplicate → enrich → qualify → research → angle → personalize → send → webhook → classify → follow-up

## Workflow Steps

1. **Normalize** (`lib/normalization`)
   - Standardize company names (remove Ltd., Inc., &, etc.)
   - Normalize phone formats
   - Validate email addresses
   - Remove special characters from postcodes

2. **Deduplicate** (`prospecting/deduplication`)
   - Exact match on email + company name
   - Fuzzy match on company name + postcode
   - Flag duplicates, keep canonical record

3. **Enrich** (`prospecting/enrichment`, `lib/enrichment`)
   - LinkedIn company data (size, industry, founding, revenue)
   - Email finder (verify + find decision makers)
   - Phone lookup
   - Recent news/funding data

4. **Qualify** (`prospecting/qualification`)
   - Score against ICP template
   - Company size check
   - Revenue estimate
   - Industry keyword match
   - Exclusion list check

5. **Score ICP** (`lib/scoring`)
   - Calculate 0-100 fit score
   - Prioritize by score
   - Filter by threshold (default 65)

6. **Research** (`database-reactivation/research`)
   - Generate 2-3 sentence company summary
   - Identify recent developments
   - Note deal size estimates

7. **Generate Angle** (`lib/personalization`)
   - Create company-specific angle
   - Use research + ICP vertical
   - Make it specific to their situation

8. **Personalize Email** (`outreach/personalization`)
   - Use angle from step 7
   - Insert company name, person name
   - Add specific details from research
   - Use configured email variant

9. **Campaign Queue** (`outreach/campaign-builder`)
   - Prepare batch for sending
   - Set send times (optimal day/time from ICP)
   - Add tracking parameters

10. **Send** (`integrations/email`)
    - SendGrid / Mailgun / AWS SES
    - Add reply tracking webhook URL
    - Log send event

11. **Reply Webhook** (`integrations/webhooks`)
    - Capture email replies in real-time
    - Store in database
    - Trigger classification

12. **Classify Reply** (`outreach/reply-classifier`)
    - AI classification: positive / maybe / negative
    - Extract sentiment
    - Determine next action

13. **Route to Sequence** (`outreach/sequences`)
    - Positive → book appointment workflow
    - Maybe → follow-up email
    - Negative → stop

14. **Book Appointment** (`outreach/analytics`, `integrations/ghl`)
    - Sync positive replies to GHL
    - Create pipeline stage
    - Set for sales team follow-up

## Configuration

See `config/templates/icp-template.json` for:
- ICP definition (size, revenue, keywords)
- Personalization fields
- Email variants (A/B/C)
- Sequence timing
- Optimal send times
- Target metrics

## Testing

Before sending to real companies:

```
1. Run against synthetic CSV (fake companies)
2. Use test email addresses
3. Verify normalization output
4. Check enrichment data
5. Review personalized emails
6. Test webhook for replies
7. Verify classification accuracy
```

## Metrics Tracked

For experimentation system:
- Send time and day
- Email variant
- Open rate
- Reply rate
- Reply sentiment
- Appointment booking
- Quote value
- Sale closed
- Revenue attributed

## Expected Performance (Targets)

- Appointments per 100 leads: 8
- Close rate: 25%
- Average deal value: £5,000
- Revenue per 100 leads: £10,000

## Database Schema

See `data/schemas/lead.schema.json` and `data/schemas/experiment.schema.json`

## Integration Dependencies

- Email provider (SendGrid)
- LinkedIn data API (optional)
- Email finder service (Hunter.io, RocketReach)
- GoHighLevel (appointment sync)
