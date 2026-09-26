# Conversations

Support Portal: https://help.gohighlevel.com/support/solutions/48000449587

Unified inbox covering SMS/MMS, email, phone, Facebook/Instagram, and web
chat. For Velarqo, the relevant slice is reply capture for the cold-outreach
loop.

## Relevant webhooks

`InboundMessage`, `OutboundMessage`, `ConversationUnreadWebhook`,
`LCEmailStats` — see `api/WEBHOOKS.md`.

## Design decision this pack flags for the team

Velarqo's cold-outreach pipeline currently assumes emails send through a
direct provider (SendGrid/Mailgun — see `pipelines/cold_outreach/README.md`)
with GHL entered only after a positive reply. An alternative is sending
*through* GHL's own email/conversation channel so replies land natively in
GHL's inbox for the client's sales team.

Trade-off:

- **Direct provider + sync-on-positive-reply** (current design): Velarqo
  controls deliverability/warm-up independently per `communications/`, and
  the cold-outreach infra is portable across CRMs — matches
  `VELARQO_PRIORITY.md`'s "keep cold-outreach infra outside GHL if it isn't
  a client-owned GHL channel" guidance.
- **Send through GHL conversations**: client's sales team sees everything
  in one inbox without a sync step, but ties outreach infra to GHL and to
  GHL's own deliverability/rate-limit envelope (`api/RATE_LIMITS.md`).

No code change needed yet — `outreach/reply_classifier` and
`lib/tracking/experiments.py` work the same either way. Revisit this when
a real client's sales-team workflow requirements are known.
