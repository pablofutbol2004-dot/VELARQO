# CLAUDE.md

## The one rule: two businesses, never conflate them

Everything in this repo belongs to exactly one of two sides. Before touching
any code, data, copy, offer, niche or legal question, decide which side it is.

| | **Velarqo (our business)** | **Clients (the businesses we work for)** |
|---|---|---|
| Who | Velarqo itself | Signed trade businesses (window/door installers, kitchen fitters, ...) |
| Selling to | Trade businesses (B2B) | Their own customers, mostly homeowners (B2C) |
| Offer | Velarqo's service to the trade business | The client's offer to its customer (re-quote, reschedule, ...) |
| "Niche" | Which trades Velarqo targets | Which customer segments the client has (lost, quoted, no-show, ...) |
| Data | Prospect leads we sourced (OSM, Companies House, websites) | The client's customer database, which they hand to us |
| Send channel | Velarqo's own mailbox: Gmail / Outlook (`integrations/email/`) | Client's GHL account (`integrations/ghl/`) |
| Pipelines | `prospecting/`, `outreach/`, `pipelines/cold_outreach/`, `pipelines/uk_universe/` | `client_onboarding/`, `database_reactivation/`, `pipelines/database_reactivation/`, `reporting/` |
| Our data-protection role | Controller | Processor, acting for the client (the client is controller) |
| Main law | PECR B2B rules + UK GDPR legitimate interests. Sole traders and partnerships count as individuals under PECR: no marketing email without consent | PECR B2C rules: consent or soft opt-in from the client's own customer relationship. We need a processor agreement (DPA) with each client |

`pipelines/experimentation/` and `lib/` are shared by both sides. Every
record and metric they handle must still say which side it belongs to, and
the two must never be mixed in one dataset.

### Consequences

- Never use Velarqo's offer, sender identity, suppression list or mailbox for
  a client, and never use the client's for Velarqo.
- Suppression and opt-outs are kept per side and per client. Someone who
  unsubscribes from one client is not unsubscribed from Velarqo or from
  other clients, and the reverse is also true. Never merge the lists.
- Each client's data is isolated from other clients and from Velarqo's
  prospect data.
- When something is ambiguous (for example "the offer", "our niches",
  "compliance"), ask which side is meant, or answer for both sides separately.

## Sources of truth

Offers, niches, identity and the law live in `truth/`, split by side
(`truth/velarqo/`, `truth/clients/<client-id>/`, `truth/compliance/`).
Read them via `lib/truth.py`. Don't hard-code an offer, niche or legal
rule anywhere else; `tests/integration/test_truth.py` catches drift. A
`TODO` value is a fact the owner hasn't supplied: never send on one.

## Status notes

- Python 3.12+ is required (the code uses nested f-string quotes).
- `ARCHITECTURE.md` predates the send-channel decision: its GHL-as-sender
  flow is wrong for Velarqo's own outreach (see the correction at its top).
- `docs/ghl/VELARQO_PRIORITY.md` is referenced in README but does not exist.
- `config/templates/icp-template.json` is the Windows UK ICP (misleading name).
