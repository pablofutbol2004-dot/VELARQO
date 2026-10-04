# GoHighLevel & delivery infrastructure: topic digest (150 videos)

- **Source:** ChatGPT's analysis of `velarqo_research/5_gohighlevel.zip` (2026-10-04), ~868k words.
- **Bias:**
  - 113 of 150 videos are Clay Lawrence, so this is mostly *one operator's GHL system*.
  - Many GHL creators earn affiliate fees, so the useful videos are heavy users admitting traps and limits.
  - ~15 videos cover US A2P SMS registration, which doesn't apply to the UK.
- **Verification (Claude, 2026-10-04):** 8 confirmed, 1 not found.
  - **Clay, "The GoHighLevel Trap"** [azmw3X6lSNc, ohYyBDka4m0]: "I literally wasted probably a year or a year and a half of progress… I had the illusion of progress."
  - **Clay:** spend "2 to 5 days really diving deep on learning how to deliver… anything over 2 to 5 days you're just guessing" [azmw3X6lSNc].
  - **Clay:** "I don't own a software. I own a highly leveraged service" [a9LexjdGFAg]. Little support is needed "because they're not logging in" [CHxt2VDkBEw].
  - **Clay:** sell it as an add-on, "don't change your CRM, don't change your booking system… We'll get integrated into what you're doing" [LE2n7Aajsfg].
  - **Clay:** ~$1,800–2,000 a month in usage (texts, emails, AI) is "rebilled to our clients at cost" [CHxt2VDkBEw]. That's variable delivery cost, not a hidden fee.
  - **Kai Stone:** "The word custom should not even be in your vocabulary." His nuance, which ChatGPT left out: **"at the beginning, 0 to five clients, do all the custom [stuff] in the world… because you're just learning"** [Db7W9Bc95jY, X0zf5foA6ug].
  - **Austin's DB reactivation:** reply yes → internal notification plus opportunity update; reply no → polite "can we follow up in a few months?" [mu9OWiLSZxk]. That's simple branching with a human, no AI agent.
  - **Not found:** Clay's "30–40% of clients get custom tweaks".
  - External (from ChatGPT, not re-checked): GHL plans are $97/$297/$497, there's a modern API (v1 ended support at end of 2025), usage is billed through a wallet and can be rebilled, and the DPA covers UK GDPR but the customer stays responsible for consent and legal basis.

## Core finding
**Velarqo is not a GHL reseller and not a CRM company.** Own the **intelligence layer**: which homeowner opportunity needs what action, when, why, what happened, and whether it created *incremental* revenue. Plug that into whatever CRM and communication rails make sense.

**The launch lesson is the trap itself.** Building CSS, dashboards, snapshots and workflows feels like progress while nobody is buying. The Velarqo version: Claude Code builds a Supabase schema, dashboard, agents, portal and attribution engine, and October ends with 0 installers contacted. **Learn delivery for days, not months, then spend most of your effort acquiring customers.**

## Architecture: four layers
| Layer | What | Stance |
|---|---|---|
| **Core** (own) | Data model, lifecycle state, eligibility, segmentation, reply classification, experiments, attribution, scoring, cross-client benchmarks, leakage diagnostics | Build. This is where proprietary knowledge compounds. |
| **Connectors** (replaceable) | CSV import, client CRM adapters (GHL, HubSpot, glazing software), webhooks/API | Build each adapter **only when several clients need it**. CSV is fine for the first pilots. |
| **Rails** (commodity) | SMS, WhatsApp, email, telephony, calendar, auth, hosting, LLM APIs | Buy. Never build an SMS gateway or a calendar. |
| **Interface** (minimal) | Internal admin → weekly client report → salesperson "today" list → portal only if usage proves it | Don't build a dashboard just because SaaS has one. |

**Build-vs-buy rule.** Buy what many vendors already do well, doesn't differentiate you, is expensive to get wrong, or is annoying to maintain. Build what encodes proprietary knowledge, what existing tools get wrong, and what improves with cross-client data. **Claude makes software cheap to create, not free to operate:** hosting, tokens, webhooks, Meta apps, bugs and maintenance all cost something.

## Principles
1. **Never make the installer replace their CRM.** "Don't change anything; we integrate with what you use." Map their statuses (e.g. `JobStatusID=47`) to Velarqo concepts (ACTIVE / WON / LOST / DORMANT / DO_NOT_CONTACT) so integrations stay swappable.
2. **The best product is invisible.** Clients shouldn't need to log in. The salesperson just gets "Sarah Jones, old quote from March, interested again, wants a survey Tuesday afternoon". At most, a TODAY list: who to call, who replied, surveys tomorrow, quotes stalled 14 days, "contact in January".
3. **GHL is legitimate infrastructure, not the product.** Use it as the client's own CRM if they have one (9/10). Use it as a fast way to deliver a *signed* pilot if it saves 36 hours (8/10; ~€300/mo is cheap next to your time). **Don't subscribe before there's demand.** Keep business logic in Velarqo, explicit, like `QUOTE_STALLED_14D → sequence B`. Don't bury it in 200 opaque GHL workflows (lock-in).
4. **Standard core, bounded configuration.**
   - Configurable: wording, service area, products, timing thresholds, routing, calendar, brand voice, eligibility rules.
   - Never forked per client: lifecycle model, attribution, reporting schema, event architecture, campaign engine.
   - Make it a reusable "W&D base config v3" once something works. Kai's caveat applies: for clients 0–5, custom is fine because you're learning.
5. **Onboarding is delivery** (~98 of 150 transcripts mention it). The pilot checklist:
   1. Data access / export
   2. Jointly define "dormant"
   3. Field mapping (quote value, status, date, source, contacts)
   4. Exclusions (active, sold, invalid, opt-outs)
   5. Sending identity, channel and message
   6. Who receives interested homeowners
   7. Which calendar
   8. **Written attribution rule**
   9. Test contacts
   10. Small first cohort, then scale
6. **Dirty data is the hidden monster:** duplicates, shared numbers, malformed phones, stale statuses, already-sold jobs, several quotes per homeowner, no lost reason, unclear marketing consent. **Turning messy contractor data into usable commercial data is real technical value.**
7. **Track cost per event from day one:** SMS, WhatsApp, voice, email, LLM tokens, enrichment, hosting. That gives contribution margin per client and cost per recovered opportunity. Never sell unlimited "AI everything".
8. **Retention comes from integration, not lock-in:** once every new lead and quote flows through the recovery layer, removing it makes something useful stop. CSV pilot → live CRM connection is the path from pilot to recurring revenue.
9. **GHL doesn't solve compliance.** "GHL lets us send it" ≠ "we're allowed to send it". UK PECR/GDPR review is still pending.

## V1 for the first pilot (keep it this small)
Client export → Python/Claude-assisted cleaning → a small DB (contact, opportunity, cohort, touch/event, appointment, outcome) → simple campaign sender through a provider API → replies into alerts → **a human qualifies** → client calendar → results logged → weekly report.

**Acceptance criteria:**
1. Import the agreed cohort
2. Dedupe
3. Exclude ineligible and prohibited records
4. Keep the source IDs
5. Send controlled messages
6. Detect replies
7. Stop automation correctly
8. Route positive or ambiguous replies to a human
9. Log every event
10. Record bookings
11. Update outcomes
12. Produce an audit/report

**No AI agent needed for V1.** Yes/no branching plus a human for nuanced replies gets the signal. Build classification (interested now, future timing, price objection, already bought, moved, wrong contact, complaint…) **after ~5,000 real homeowner replies**, from real data instead of invented prompts.

**Next milestone: one real UK installer, one ugly export, one working pilot.** That dataset should shape the architecture, not YouTube or GHL.

## Ratings
| Use | Score |
|---|---|
| Velarqo-owned canonical data/intelligence layer | 9.5 |
| GHL as the client's existing CRM (adapter) | 9 |
| GHL as temporary rapid-delivery engine for a signed pilot | 8 |
| GHL as a communication/workflow adapter | 8 |
| All Velarqo logic inside GHL workflows | 4 |
| Velarqo = white-label GHL SaaS | 3 |
| Force clients to migrate into GHL | 2 |
| Rebuild every GHL feature ourselves | 2 |
