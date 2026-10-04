# Acquisition state machine

## Company-level states

| State | Meaning | Exit condition |
|---|---|---|
| DISCOVERED | Raw candidate from an allowed discovery source | source evidence saved |
| ENTITY_VERIFIED | Legal entity matched where possible | company number/type/status or explicit unresolved reason |
| COMPANY_QUALIFIED | Meets current ICP minimums | qualification rule version stored |
| WEBSITE_RESOLVED | Canonical operating domain/website identified | confidence + evidence stored |
| PERSON_RESOLVED | Relevant decision maker/person identified if needed | role evidence stored |
| CONTACT_RESOLVED | One or more candidate contact points | provenance stored |
| COMPLIANCE_ROUTED | Legal/operational route assigned | `send_allowed=true/false/review` |
| EMAIL_VERIFIED | Address status checked | provider result + checked_at stored |
| SCORED | Acquisition score computed | score version stored |
| COHORTED | Assigned to experiment cohort | cohort frozen |
| READY_TO_SEND | All hard gates passed | queue row created |
| SENT | Message attempted | immutable send event |
| REPLIED | Reply received | reply classified |
| CONVERSATION | Real sales/research conversation exists | evidence captured |
| EXPORT | Client data/export obtained | hand off to Pass 12 |
| PILOT | Client-1 pilot started | Pass 12 governs |

## Terminal / hold states

- `DISQUALIFIED`: wrong business, dissolved, supplier/manufacturer-only, unsuitable size/model, etc.
- `SUPPRESSED`: business/contact objected or internal do-not-contact.
- `COMPLIANCE_REVIEW`: entity/contact route uncertain.
- `NO_CONTACT_FOUND`: company can remain in universe for future enrichment.
- `BOUNCE_HARD`: contact point disabled; company remains eligible for alternate route.
- `DUPLICATE`: merged into canonical identity.

Never delete terminal states from history. They prevent reacquisition loops and repeated mistakes.
