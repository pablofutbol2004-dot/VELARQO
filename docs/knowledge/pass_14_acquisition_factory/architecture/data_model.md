# Canonical data model

## Identity hierarchy

`company → person → contact_point → campaign_member → send_event → reply_event → conversation`

A company may have many people. A person may have multiple contact points. A contact point may be used in multiple experiments, but suppression applies across experiments.

## Stable identifiers

- `company_id`: internal UUID; never use company name as identity.
- `company_number`: Companies House number when matched.
- `person_id`: internal UUID.
- `contact_id`: internal UUID per email/phone/contact endpoint.
- `campaign_member_id`: one company/contact in one frozen cohort.
- `event_id`: immutable event UUID.

## Evidence pattern

Every non-user-entered factual field should ideally carry:

- `source_type`
- `source_url`
- `source_record_id`
- `observed_at`
- `confidence`
- `raw_value`

Do not overwrite conflicting source values silently. Canonicalization chooses a current value while source evidence remains available.

## PII minimization

Store only what is useful to qualification/contacting. Do not collect birthdays, personal addresses, family information or unrelated social/profile data because it is available.
