# Monthly setup checklist: what must exist in GoHighLevel per client

What one person has to build and switch on in GoHighLevel (GHL) to deliver
each monthly tier (`docs/PRICING.md`, "The monthly product"; client wording
in `11_monthly_terms.md`). Our database stays the record of truth (pilot
IDs, homeowner states, booked-survey log, invoices: `WORKFLOW.md`); GHL
does the sending, replies, calls and calendar.

Status: nothing here is built yet. The first pilot builds the Chase half
(items 1-9) once, as a snapshot; every later client is a copy. Items
marked **verify** are GHL/Twilio facts to check on the live account before
the first client, not assumptions to build on.

## 0. Once, at agency level (before client 1)

| # | Thing | Why | Notes |
|---|---|---|---|
| 0.1 | GHL plan | Starter ($97, 3 sub-accounts) up to 3 clients; Unlimited ($297) from client 4 and for rebilling usage to clients | Plan cost table at the end. Trial at first sample, paid at first pilot (`project_ghl_timing`). |
| 0.2 | LC Phone enabled, UK regulatory bundle | UK numbers need an address and business details on file | **verify:** which address (ours in Spain, or the client's UK one) the UK bundle accepts for mobile numbers. |
| 0.3 | LC Email with velarqo.com sending domain, DKIM/SPF | Email touches go from the client's name but through our domain or theirs | Per client: ask whether we send from their domain (needs their DNS) or from `[installer]@send.velarqo.com` with reply-to their inbox. |
| 0.4 | The **Velarqo snapshot** | One build, copied into every sub-account | Everything in sections 1 and 2 lives in it. Re-snapshot after every change. |
| 0.5 | Agency setting: duplicate contacts off; workflow re-entry off on every sending workflow | Same person never enrolled twice; a repeated tag never resends | Already required for the pilot (`README.md`, row 11). |
| 0.6 | Webhooks → our endpoint | Reply, STOP, booking, outcome events into our DB | `docs/ghl/api/WEBHOOKS.md`. Return 200 only after commit. |

## 1. Per client, both tiers (Chase is the base)

| # | Thing | Built how | Done when |
|---|---|---|---|
| 1.1 | **Sub-account from the snapshot** | Create location, load snapshot, name `vq-<client_slug>` | Custom fields, pipeline, calendars, workflows all present; test contact runs end to end to Pablo's own phone |
| 1.2 | **Custom fields** | `homeowner_key`, `pilot_id`/`plan`, `quote_date`, `product`, `source` (quote / missed call / enquiry / requote), `wave_id`, `outcome` | Our upsert writes them; nothing keyed on name or phone alone |
| 1.3 | **UK number** (mobile, SMS-capable) | LC Phone → buy UK number; **verify** that a UK 07 mobile number is offered with two-way SMS (UK 01/02 landline numbers don't take SMS) and the monthly price (about £1.50) | A text from Pablo's phone to the number lands in the conversation and a reply comes back |
| 1.4 | **STOP handling** | GHL's built-in opt-out keywords (STOP, UNSUBSCRIBE, etc.) set the contact to DND for SMS; our webhook also writes `opted_out` to suppression, which beats everything. Every text ends "Reply STOP to opt out" (`08`) | Send STOP from the test phone: DND set in GHL, suppression row in our DB, next enrol attempt refused |
| 1.5 | **Quiet hours** | Every sending workflow waits for the window 9am-7pm Europe/London, Mon-Sat, before each send; bank holidays added by hand each quarter as a "do not send" condition | A message queued at 8pm Saturday goes at 9am Monday |
| 1.6 | **Quote intake route** (how a new quote reaches us the day it's sent) | Pick one per client, simplest first: (a) the installer forwards the quote email to a client inbox we read and enter by hand or script; (b) a weekly CSV export from their job software (Tradify, Powered Now etc.) imported with `delivery.pilot import`; (c) a short web form (GHL form) the office fills in; (d) later, an email parser or Zapier into the GHL inbound webhook. GHL does not parse emails on its own | A quote sent today is a contact tagged `vq-chase` by the next working morning |
| 1.7 | **Chase sequence workflow** | 5 touches over about 30 days (text day 0, text day 3, email day 7, text day 14, text day 28), from the approved wording; stops the moment the contact replies, books or opts out; re-entry off | Approved text hashes match `09`; test contact receives the sequence in order and stops on a reply |
| 1.8 | **Booking link / calendar** | One GHL calendar per client ("Survey"), slots from the intake form, 1 slot per hour, confirmation text and email at booking, reminder text the day before and 2 hours before; calendar invite to the installer's email | A test booking appears in their diary and in our DB via the appointment webhook |
| 1.9 | **Booked-survey log** | A booking is billable only when our DB has the appointment event *and* the homeowner's state is `booked` from a `vq-` tagged contact; the invoice lines come from the DB, not from the GHL calendar | `WORKFLOW.md` step 9: one invoice per (client, month), lines = bookings not yet invoiced, credits by booking ID |
| 1.10 | **Usage cap** | Two layers: (a) a sub-account wallet with auto-recharge **off** and a monthly top-up equal to the tier's usage estimate × 2 (so a runaway workflow stops itself); (b) our DB cap on sends per client per day (`send-wave` already stops on pause). **verify** the wallet/credit setting available on the plan we're on | A workflow that tries to send 1,000 texts stops when the wallet is empty, and we get an email |
| 1.11 | **Weekly booking cap** | A counter per client per ISO week in our DB; when reached, the reply script offers next-week dates only; the calendar's availability for the current week is closed by hand if needed | Cap set on the signed sheet; raised only by the client's email, logged |
| 1.12 | **Review request** | Workflow triggered by `outcome = won + job finished`: one text and one email asking for a Google review, with the installer's review link | Only fires when the installer records the job as finished |
| 1.13 | **Monthly report** | `10_weekly_report_template.md` run monthly: counts only, invoice section, no percentages in the headline | Sent with the invoice on the 1st |

## 2. Per client, Chase + Answer only

| # | Thing | Built how | Done when |
|---|---|---|---|
| 2.1 | **Call diversion** | The installer dials the divert-on-no-answer / divert-on-busy code on their main mobile or office line to the Velarqo UK number (they keep their own number). Alternative: they put the Velarqo number on adverts and the GHL number forwards to them | A call to their number that rings out lands on the GHL number |
| 2.2 | **Missed-call text-back workflow** | Trigger: inbound call not answered (or voicemail) → wait 60 seconds → text from the UK number in the installer's name ("Sorry we missed you, it's [sender] at [Installer]. What's it about and I'll call you back?") → notify Pablo → conversation handled by a person within the hour | A missed test call gets a text within a minute and shows in Pablo's inbox |
| 2.3 | **Enquiry capture** | Every source the client has: web form (GHL form embedded, or a webhook from their current form), email enquiries forwarded to the client inbox, Facebook lead forms if they run them, texts to the UK number. Each creates a contact tagged `vq-enquiry` with `source` set | Each source tested with a real submission |
| 2.4 | **Instant-reply workflow** | Trigger: new `vq-enquiry` contact in hours → within 5 minutes a text and/or email in the installer's name acknowledging the enquiry and offering survey times (booking link) → notify Pablo → person follows up within the hour | Template, not AI, for the first clients. Measured from the enquiry timestamp to the first outbound message in the DB |
| 2.5 | **Out-of-hours reply** | Same trigger outside 9am-7pm Mon-Sat: one automatic text saying when someone will call back (next working morning) and asking the two or three questions from the intake (what, where, when); nothing else until the window opens | Sent once, no repeats, no booking push at night |
| 2.6 | **Quarterly re-chase** | Every 3 months, the client's quotes that have gone 3+ months quiet are exported, run through eligibility and holdout exactly as the pilot (`delivery.pilot import / freeze / send-wave`), under a new wave ID | Same stop conditions as the pilot (`04`, section 8) |
| 2.7 | **AI (optional, off by default)** | Conversation AI on pay-as-you-go (about 1.5p a message) for out-of-hours qualification only, after the client has seen the template version run for a month. The flat AI Employee add-on (about £75 a sub-account a month) is off unless a client pays extra for it | Documented in the client folder when switched on; every AI reply logged |
| 2.8 | **Intake additions** | On the intake form: which line to divert, enquiry sources, out-of-hours questions, call-back promise wording, what the installer wants said about price on the phone (nothing, usually) | Signed with the sheet |

## 3. Per-client checks before going live (both tiers)

- [ ] Test contact = Pablo's own UK-reachable phone: full sequence, STOP,
      booking, reminder, review request all received and logged.
- [ ] Quiet hours confirmed by a send queued outside the window.
- [ ] Wallet cap set; our daily send cap set; weekly booking cap from the
      sheet entered.
- [ ] Approved wording hashes in `09` match the workflow texts.
- [ ] Client's do-not-contact list loaded into suppression.
- [ ] Data processing agreement signed; client folder created outside git.
- [ ] Monthly invoice date and start date in the DB; first invoice pro rata.
- [ ] Chase + Answer: diversion dialled and tested; every enquiry source
      fires a tagged contact; out-of-hours reply seen once.

## 4. GHL plan cost at each client count

USD prices from `docs/knowledge/web_research/2026-10-10_monthly_product_renewables.md`;
pounds at about $1.30 to £1, estimates. Usage (texts, number, email) is on
top and is in the margin table in `docs/PRICING.md`.

| Clients | Plan needed | Plan cost / month | Plan cost per client |
|---:|---|---:|---:|
| 1-3 | Starter ($97) | about £75 | £75 / £37 / £25 |
| 4-5 | Unlimited ($297) | about £230 | £58 / £46 |
| 10 | Unlimited | about £230 | £23 |
| 20 | Unlimited | about £230 | £12 |

Rebilling (charging each client's usage back automatically) needs
Unlimited; on Starter we absorb usage inside the monthly fee, which the
margin table already assumes. Agency Pro ($497, software resale) isn't
needed for either tier.

## 5. Time per client (estimates, to be replaced by the first month's log)

| Task | Chase | Chase + Answer |
|---|---:|---:|
| Set-up from snapshot, number, intake, tests | 3 h once | 5 h once |
| Entering new quotes (route a or b) | 1 h / month | 1 h / month |
| Answering replies and booking | 2 h / month | 4 h / month |
| Missed calls and enquiries | – | 1.5 h / month |
| Report and invoice | 0.5 h / month | 0.5 h / month |
| Quarterly re-chase (spread) | – | 0.5 h / month |
| **Running total** | **about 4 h / month** | **about 7 h / month** |

Log real minutes per client from month one; the margin table and the price
anchors move on these numbers, not on the guesses above.
