# 05 — Contact resolution and verification

## Canonical process

1. identify canonical domain
2. prefer publicly stated company contact endpoints
3. resolve named work email only when appropriate
4. record exact source/provenance
5. verify syntax/domain/mailbox with a replaceable verifier
6. classify result
7. never send to `invalid`; isolate `accept_all/unknown` for controlled testing

## Provider abstraction

A verifier adapter should return canonical fields:

`provider, provider_status, canonical_status, confidence, checked_at, raw_response_ref`

Canonical statuses:

- `valid`
- `invalid`
- `accept_all`
- `unknown`
- `risky`
- `not_checked`

Hunter is one possible adapter, not the database itself.

## Freshness

Verification decays. Recheck stale addresses before reuse after a long pause or when provider results are ambiguous.
