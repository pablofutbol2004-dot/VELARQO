# Email sender domains

Support Portal (Email section): https://help.gohighlevel.com/support/solutions/48000449563

Each client/Location sending email through GHL needs its own verified
sending domain with SPF/DKIM/DMARC records set at the DNS level. This is a
per-client setup step in `client_onboarding/intake/`, not something Velarqo
can automate away — it requires access to the client's DNS.

## Onboarding checklist item

Add to the client onboarding intake flow (`client_onboarding/intake/`):

1. Confirm client has a domain available for sending (not their primary
   corporate domain if avoidable — a dedicated subdomain isolates reputation
   risk from their main mail).
2. Verify SPF/DKIM/DMARC records are added and propagated before campaign
   go-live, not after.
3. Record the verified sending domain against the client record so the
   cold-outreach pipeline can refuse to send if the domain isn't verified.

This isn't built into `pipelines/cold_outreach/` yet — it's a real
integration point once email actually sends through a live provider,
not just the template-generation stage that exists today.
