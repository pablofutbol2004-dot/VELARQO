# Contacts

Support Portal: https://help.gohighlevel.com/support/solutions/155000000123
API surface: `api/official-docs/apps/v3/contacts-v3.json`

## Key endpoints (v3)

- `POST /contacts/upsert` — idempotent create-or-update, matched by the
  Location's configured "Allow Duplicate Contact" setting (email/phone
  priority order). **This is the endpoint for `integrations/ghl/` to use**,
  not separate create/update calls — matches the idempotency rule in
  `AGENTS_GHL.md`.
- `POST /contacts/search`, `POST /contacts/search/duplicate`
- `GET/PUT/DELETE /contacts/{contactId}`
- `/contacts/{contactId}/tags`, `/notes`, `/tasks`, `/appointments`,
  `/campaigns/{campaignId}`, `/workflow/{workflowId}`
- `POST /contacts/bulk/tags/update/{type}`, `POST /contacts/bulk/business`

## Upsert request (only `locationId` is required; everything else optional)

`firstName`, `lastName`, `name`, `email`, `phone`, `address1`, `city`,
`state`, `postalCode`, `website`, `companyName`, `tags`, `customFields`,
`source`, `dnd`, `dndSettings`/`inboundDndSettings`, `assignedTo`,
`createNewIfDuplicateAllowed`.

Response: `{ new: bool, contact: { id, ... }, traceId }` — the `contact.id`
is what should be persisted as `lead.ghl_contact_id` /
`reactivation_record`'s GHL id.

## Mapping onto Velarqo's schema

| Velarqo field (`data/schemas/lead.schema.json`) | GHL upsert field |
|---|---|
| `company_name` | `companyName` |
| `email` | `email` |
| `phone` | `phone` |
| `postcode` | `postalCode` |
| `website` | `website` |
| `lead_source` | `source` |
| `icp_score`, `research_summary`, `angle` | `customFields` (define custom field IDs per Location — these are Velarqo-specific, not native GHL fields) |
| — | `tags` — use for segment/qualification state (e.g. `qualified`, `duplicate`) so sales reps see it in the GHL UI without a custom field lookup |

`duplicate_of` stays Velarqo-side only — don't push duplicate records to
GHL at all; suppress them before the upsert call.

## DND

`dnd` / `dndSettings` / `inboundDndSettings` are per-channel. A
`ContactDndUpdate` webhook (see `api/WEBHOOKS.md`) must flip Velarqo's local
suppression state immediately — GHL is the source of truth for consent,
not Velarqo.
