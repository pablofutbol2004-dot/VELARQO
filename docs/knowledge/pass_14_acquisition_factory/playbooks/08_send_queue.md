# 08 — Send queue

## Ready-to-send hard gates

- `icp_pass=true`
- `send_allowed=true`
- `suppressed=false`
- contact verification acceptable for the current policy
- source/provenance present
- experiment cohort assigned
- sender mailbox/domain passes Pass 13 outbound gate
- no existing active conversation with same company
- no duplicate send in cooling window

## Idempotency key

Recommended:
`company_id + contact_id + campaign_id + step_number`

Reject duplicate idempotency keys before enqueue.

## Queue fields

- campaign_id
- cohort_id
- company_id
- person_id/contact_id
- sequence_step
- scheduled_at
- sender_mailbox
- template_version
- idempotency_key

Sending provider state is downstream; the canonical queue remains yours.
