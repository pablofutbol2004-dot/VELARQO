# Webhooks

Canonical category page: https://marketplace.gohighlevel.com/docs/category/webhook/
Event payload references: `docs/ghl/api/official-docs/docs/webhook events/*.md`

## Event families relevant to Velarqo

| Family | Events (subset) | Velarqo use |
|---|---|---|
| Contacts | ContactCreate, ContactUpdate, ContactDelete, ContactDndUpdate, ContactTagUpdate | Sync GHL-side edits back into `lead`/`reactivation_record`; respect DND flips |
| Opportunities | OpportunityCreate/Update/Delete, OpportunityStageUpdate, OpportunityStatusUpdate, OpportunityMonetaryValueUpdate, OpportunityAssignedToUpdate | Drives `experiment_result` outcomes: appointment -> quote -> sale -> revenue |
| Appointments | AppointmentCreate, AppointmentUpdate, AppointmentDelete | `record_appointment()` in `lib/tracking/experiments.py` |
| Conversations | InboundMessage, OutboundMessage, ConversationUnreadWebhook, LCEmailStats | Reply capture — feeds `integrations/webhooks/reply_webhook.py` instead of (or alongside) a direct email-provider webhook |
| Invoices/Orders | InvoiceCreate/Paid/Void, OrderCreate/StatusUpdate | Revenue attribution if Velarqo bills through GHL |
| Tasks/Notes | TaskCreate/Complete, NoteCreate | Optional — sales-team activity signal, not core to the three pipelines |
| App lifecycle | AppInstall, AppUninstall, PlanChange | Only relevant if Velarqo becomes a Marketplace app |

Every event payload includes `type` and `locationId` — always check `type`
to dispatch, and always scope by `locationId` (= client) even in a
single-tenant deployment, since it's the field that will matter the moment
Velarqo has more than one client account wired up.

## Design rules (from `AGENTS_GHL.md`, applied concretely)

1. **Verify the request is genuinely from GHL** before processing — check
   whatever signature/secret mechanism the current Developer Portal webhook
   setup provides (varies by webhook config type; confirm at build time,
   don't assume a specific header name from memory).
2. **Idempotency**: every event has an entity `id` (contact id, opportunity
   id, etc.) but not always a delivery id. De-dupe on
   `(type, id, updated-field-if-present)` within a short window, since
   retries can resend the same event.
3. **Out-of-order delivery is possible.** Don't assume `ContactUpdate`
   always arrives after `ContactCreate` for the same id — upsert-style
   handling (last-write-wins on a timestamp field) is safer than assuming
   ordering.
4. **Map straight into the existing schema, don't invent a parallel one.**
   `ContactCreate`/`ContactUpdate` -> upsert into `lead` or
   `reactivation_record` keyed on `ghl_contact_id`; `OpportunityStageUpdate`
   -> update the matching `experiment_result` row's segment/status, not a
   new table.
5. **Respect DND on receipt, not just on send.** A `ContactDndUpdate` event
   means stop queuing further sends for that contact immediately, not on
   the next campaign build.

## Where this plugs into the existing pipeline code

- `integrations/webhooks/reply_webhook.py` currently assumes a raw email
  reply payload. A GHL-backed conversation webhook (`InboundMessage`)
  should get its own handler that extracts the message body the same way
  and calls the same `classify_reply()` / `record_reply()` functions —
  don't duplicate the classification logic per source.
- `lib/tracking/experiments.py` (`record_appointment`, `record_sale`)
  should be called from `OpportunityStageUpdate` / `OpportunityStatusUpdate`
  handlers once a GHL integration exists, rather than only from the
  synthetic CLI flow used today.
