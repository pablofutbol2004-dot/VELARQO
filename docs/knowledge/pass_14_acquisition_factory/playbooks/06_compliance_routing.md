# 06 — Compliance routing

This is an operational routing layer, not legal advice.

## UK electronic-mail split

### Corporate subscriber
Examples include limited companies and LLPs. ICO guidance says the PECR consent rule for electronic mail does not apply to corporate subscribers, but identity/opt-out requirements still apply; UK GDPR still applies when personal data is processed.

Operational route:
- verify corporate status where practicable
- document lawful basis for personal-data processing when using named individuals
- provide transparency/privacy information as required
- clearly identify sender
- provide a valid opt-out
- suppress objections globally

### Individual subscriber
Sole traders and certain partnerships receive individual-level PECR protection. Do **not** route cold electronic marketing to them absent documented consent/soft-opt-in or a specifically reviewed lawful route.

### Unknown entity type
`COMPLIANCE_REVIEW`, not “probably ltd”.

## Hard blockers

- suppression match
- explicit prior objection
- invalid contact
- unresolved entity type where rules differ
- missing sender identity / opt-out mechanism
- missing source/provenance for named personal data

## Data minimization

The fact that data is public does not remove UK GDPR obligations.
