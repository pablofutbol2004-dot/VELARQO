# Provider adapters

The factory should expose internal interfaces and isolate vendor-specific payloads.

## `CompanyDiscoveryAdapter`
Input: niche/filter spec.
Output: candidate companies + source evidence.
Possible adapters: Companies House, FENSA/Certass import, existing CSV, manually curated list.

## `WebsiteResolutionAdapter`
Input: legal/trading name, address/domain hints.
Output: candidate canonical domain, confidence, evidence.

## `PersonResolutionAdapter`
Input: company + desired role categories.
Output: people + roles + provenance.
Possible adapters: company site, Hunter/Apollo/other enrichment.

## `ContactResolutionAdapter`
Input: company/person/domain.
Output: candidate contact points + source evidence.

## `EmailVerificationAdapter`
Input: email.
Output: canonical verification status + raw provider result reference.

## `SenderAdapter`
Input: queue row + rendered message.
Output: provider message id / accepted / rejected.
Sender must never decide whether a record is compliant or suppressed; it receives only `READY_TO_SEND` records.

## `ReplyAdapter`
Input: inbound provider webhook/message.
Output: normalized reply event and thread identifiers.

### Rule
A vendor outage or replacement should require swapping one adapter, not migrating the business database.
