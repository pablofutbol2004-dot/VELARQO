# Outreach log schema

Use one row per prospect/company for the initial experiment. Keep raw email/message history separately if needed.

Required fields for the summarizer:
- prospect_id
- company
- variant
- attempted
- delivered
- bounced
- reply_class (`positive`, `negative`, `optout`, `ambiguous`, `none`)
- call_booked
- call_held
- qualified
- export_requested
- export_received
- pilot_interest
- pilot_agreed

Add timestamps and richer notes in the operational system, but do not break these canonical fields.
