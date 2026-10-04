# Velarqo operating map: every step, from cold email to cash

This is the whole business as a list of actions. Each action has an owner,
a tool and a status, so nothing waits for someone to work out what to do.

**Who:** P = Pablo · C = Claude (in this repo) · S = system (runs by
itself) · I = the installer (client)

**Status:** ✅ ready now · 🔧 built, needs setup · 🛠 to build · ✍ to
write or decide

Detail lives in the linked docs. This page is the spine.

---

## Where GoHighLevel fits

**Not for finding installers.** Velarqo's own cold email runs on our send
engine + Google Workspace (built, cheaper, already holds the test data).

**Yes for delivering to clients:** texting and emailing the installer's old
homeowners, two-way conversations, booking surveys into the installer's
diary, reminders, and a pipeline (booked → attended → won) the installer
can see. One GHL **sub-account per installer**, cloned from one Velarqo
**snapshot** (a template of the workflows, calendar, pipeline and fields).

**When:**

| Trigger | GHL action |
|---|---|
| Before any installer is interested | Nothing. Don't pay for it yet. |
| **First installer sends a sample of old quotes** (step 4.1) | Start the GHL free trial. Build the snapshot while auditing the sample (needs about 3-5 days, mostly the UK SMS number and email domain checks). |
| First pilot agreed (step 5) | Move to a paid plan. Create the installer's sub-account from the snapshot. |
| 2nd and later clients | New sub-account from the snapshot in under an hour. |
| Velarqo's own calls | Use the free Google Calendar booking page (comes with Workspace), not GHL. Move it into GHL only if that gets easier later. |

Check GHL's current plan prices and UK SMS number requirements at trial
start (prices and rules change).

---

## Phase 0: Foundations (one-time)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 0.1 | Apply the send-engine database change | P approves, C applies | Supabase | 🔧 waiting for your OK |
| 0.2 | Save all work to git | P allows, C commits | git | 🔧 waiting for your OK |
| 0.3 | Buy a separate sending domain | P | Cloudflare / registrar | ✍ |
| 0.4 | Google Workspace + 2 mailboxes on it | P | Google | ✍ |
| 0.5 | SPF, DKIM, DMARC on the sending domain; DMARC on velarqo.com | P (C guides) | Cloudflare DNS | ✍ |
| 0.6 | Warm-up tool on both mailboxes, 2-3 weeks | P | Instantly/Lemwarm/Warmbox | ✍ |
| 0.7 | Google Cloud OAuth client (Internal) → `.env` | P (C guides) | Google Cloud | ✍ |
| 0.8 | `config/mailboxes.json`, `authorize-mailbox`, `test-send` | C | CLI | 🔧 |
| 0.9 | Schedule `scripts/outbound_tick.cmd` every 15 min | C | Windows Task Scheduler | 🔧 |
| 0.10 | Google Calendar booking page "15-min call with Pablo" | P | Google Calendar | ✍ |
| 0.11 | Your full name on velarqo.com (+ NIF once registered) | P supplies, C edits | website | ✍ |
| 0.12 | Register as autónomo (alta Hacienda + RETA). **Can't invoice without it** | P + gestor | gestor | ✍ needed before step 12 |
| 0.13 | Ask gestor: VAT on services to UK businesses (likely reverse charge), invoice format | P | gestor | ✍ needed before step 12 |
| 0.14 | Bank account that takes GBP (e.g. Wise) | P | Wise / bank | ✍ needed before step 12 |
| 0.15 | Pilot agreement + data processing agreement (DPA) | C drafts from `pass_03.../commercial/terms_checklist.md`, lawyer checks | doc | 🛠 needed before step 5 |

## Phase 1: Find installers (daily, automatic once set up)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 1.1 | Keep the universe fresh (re-source, re-score) monthly | C | `pipelines/uk_universe` → Supabase | ✅ |
| 1.2 | Draft next batch from `outreach_queue` with the current test | P runs | `create-cohort --experiment cold_offer_v1 --size 50` | 🔧 |
| 1.3 | Read the review CSV; `cancel` obvious misfits | P | `review` / `cancel` | 🔧 |
| 1.4 | Activate the batch; sending switch on | P | `activate`, `sending on` | 🔧 |
| 1.5 | Send in UK hours within mailbox caps, with all safety checks | S | `run` (every 15 min) | 🔧 |
| 1.6 | Read replies and bounces; suppress opt-outs; stop follow-ups | S | `run` | 🔧 |
| 1.7 | Follow-ups after 3 and 5 business days | S | `run` | 🔧 |
| 1.8 | Raise mailbox caps weekly (10 → 20 → 30) if bounces stay under 3% | P (C advises) | `config/mailboxes.json` | 🔧 |
| 1.9 | Check `status` for problems | P, 2 min/day | `status` | 🔧 |

## Phase 2: Reply → call (same day)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 2.1 | Open the replies that need you | P | `replies` | 🔧 |
| 2.2 | Answer with the matching reply (interested / how much / send info / we already chase) | P | `docs/SALES_PLAYBOOK.md` §1 | ✅ |
| 2.3 | Correct the category if the robot got it wrong; mark handled | P | `handled <id> --as positive` | 🔧 |
| 2.4 | Send the booking link or call them on their number | P | booking page (0.10) | ✍ |
| 2.5 | Log the booked call | P | `outcome <email> call_booked` | 🔧 |
| 2.6 | "Send info" one-pager, trimmed to half a page in house style | C | `pass_12.../client_handoff/pilot_one_pager.md` | 🛠 rewrite |

## Phase 3: The call → sample

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 3.1 | 5 min before: history + **which test price to quote** | P | `call-sheet <email>` | 🔧 |
| 3.2 | Run the 15-20 min call (numbers, follow-up reality, backlog, systems, data source, capacity) | P | `SALES_PLAYBOOK.md` §2 | ✅ |
| 3.3 | Ask the 3 price questions, then quote the arm's price | P | `docs/PRICING.md` P1 | ✅ |
| 3.4 | Close small: ask for 20-50 old quotes, names can be blanked out | P | `SALES_PLAYBOOK.md` §3 | ✅ |
| 3.5 | Send the export request email right after the call | P | `pass_13.../handoff/export_request.md` (rewrite in house style) | 🛠 rewrite |
| 3.6 | Log the call, price reaction and notes (volumes, job value, system) | P | `outcome <email> call_held --reaction ... --note ...` | 🔧 |
| 3.7 | If not a fit: say so, log `lost` with the reason | P | `outcome ... lost` | 🔧 |

## Phase 4: Sample audit (the free look, also offer B of the email test)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 4.1 | Receive the sample; log it. **Start the GHL trial now** (trials are short, usually about 14 days; if the pilot stalls, pause rather than pay) | P | `outcome ... sample_received` | 🔧 |
| 4.2 | Store it outside git, per-client folder | C | `clients/<id>/` (gitignored), `create_client_workspace.py` from Pass 12 | 🛠 adapt |
| 4.3 | Map columns, check quality, count by quote age / status / product | C | `client_onboarding` intake + field mapping + quality check | 🔧 extend for audit counts |
| 4.4 | Run eligibility (opt-outs, won jobs, data source, area) | C | `pass_12.../data/eligibility_decision_tree.md` | 🛠 build as a script |
| 4.5 | One-page audit result to the installer: how many look worth chasing, by age, and the plan | C drafts, P sends | audit report template | 🛠 |
| 4.6 | Book the "go through the audit" call; propose the pilot | P | booking link | ✍ |

## Phase 5: Agreement

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 5.1 | Agree in writing: what counts as a booked survey, price (from P1 arm), cap, no-show credit, weekly invoice | P | pilot agreement (0.15) | 🛠 |
| 5.2 | Sign the DPA (they own the data, we process it) | P + I | DPA (0.15) | 🛠 |
| 5.3 | Installer confirms where the homeowner data came from and sends their opt-out list | I | intake form | 🛠 |
| 5.4 | Log it | P | `outcome ... pilot_signed` | 🔧 |

## Phase 6: Onboarding the installer (1-3 days)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 6.1 | Intake: service area, products, survey slots, who attends, reply owner + response time, sender name | P + I | `pass_03.../onboarding/client_intake_v0.md` → form | 🛠 make a short form |
| 6.2 | Create the GHL sub-account from the snapshot | C/P | GHL | 🛠 snapshot to build |
| 6.3 | UK SMS number + sender email for the installer's brand | P | GHL phone / email | ✍ |
| 6.4 | Calendar connected to the installer's survey diary | P + I | GHL calendar | 🛠 |
| 6.5 | Installer approves the homeowner messages, word for word | I | message approval sheet | 🛠 |
| 6.6 | Installer gets the GHL app / notifications for new bookings | P + I | GHL | 🛠 |

## Phase 7: Data → campaign-ready (Client-1 gate)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 7.1 | Full export in; same audit as 4.3-4.4 on all records | C | scripts | 🛠 |
| 7.2 | Remove opt-outs, won jobs, current customers, out-of-area, unknown source | C | eligibility script | 🛠 |
| 7.3 | Split off a random **holdout** (not contacted, about 10-20%, agreed in the pilot terms since it's their leads) so we can prove real lift | C | `pass_12.../measurement/holdout_design.md` | 🛠 small script |
| 7.4 | Stable ID per homeowner across import → message → booking → outcome | C | Supabase + GHL contact IDs | 🛠 |
| 7.5 | Push eligible contacts to GHL with tags (quote age, product, test arm) | C | `integrations/ghl` upsert (built, never run live) | 🔧 |
| 7.6 | Run the 50-check Client-1 gate; nothing launches with an open item | C + P | `pass_12.../tools/check_client1_gate.py` | 🔧 fill in |

## Phase 8: Homeowner campaign build

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 8.1 | Write the homeowner sequence in house style (3 SMS + email, from the installer's name) | C | from `pass_03.../delivery/reactivation_sequence_v0.md` | 🛠 rewrite |
| 8.2 | Build it as a GHL workflow: send → wait → stop on reply → STOP keyword suppresses | C/P | GHL workflow in the snapshot | 🛠 |
| 8.3 | Reply handling rules: what's automatic, what goes to a human (complaints, pricing, vulnerable people) | C | `pass_03.../delivery/homeowner_reply_handling.md` | 🛠 into GHL |
| 8.4 | Booking flow: offer 2 slots → confirm → calendar → installer notified | C/P | GHL calendar + workflow | 🛠 |
| 8.5 | Reminders before the survey (day before, morning of) | C/P | GHL workflow | 🛠 |
| 8.6 | Test the whole thing on your own phone/email | P | GHL | 🛠 |

## Phase 9: Canary (first 20-30 homeowners)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 9.1 | Send to a small slice; check every single contact by hand | P | GHL | ✅ runbook `pass_12.../pilot/canary_runbook.md` |
| 9.2 | Check delivery, replies captured, STOP works, bookings land, installer notified | P | GHL | ✅ runbook |
| 9.3 | Fix, then expand. One booking is not proof it's safe | P | — | ✅ |

## Phase 10: Live pilot (daily while running)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 10.1 | Answer interested homeowners within the hour, book surveys | P (later: GHL AI with strict limits) | GHL conversations | 🛠 |
| 10.2 | Escalate complaints / pricing / sensitive replies to a person | P | GHL | 🛠 |
| 10.3 | Watch stop conditions (opt-outs, complaints, lost replies, installer can't cover slots) | P | `pass_12.../pilot/stop_conditions.md` | ✍ fill thresholds |
| 10.4 | Log your minutes per day (needed to price properly later) | P | timesheet | ✍ |

## Phase 11: Outcomes (weekly)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 11.1 | Installer marks each survey: attended / no-show / requoted / won / value | I | GHL pipeline stages | 🛠 |
| 11.2 | Pull GHL outcomes into Supabase (the record of truth) | C | GHL webhooks or API pull | 🛠 |
| 11.3 | Compare against the holdout | C | `pass_12.../tools/analyze_client1.py` | 🔧 adapt |

## Phase 12: Billing and cash

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 12.1 | Weekly list of billable surveys (by the agreed definition), no-shows credited | C | billing reconciliation sheet (`pass_12.../economics/`) | 🛠 script |
| 12.2 | Installer confirms the list | I | email | ✍ |
| 12.3 | Invoice (needs autónomo + NIF, 0.12-0.13) | P | gestor's invoicing tool | ✍ |
| 12.4 | Chase unpaid invoices at 7 and 14 days | P | email | ✍ |
| 12.5 | Record cash received and payment delay | P | unit economics sheet | 🛠 |

## Phase 13: Reporting to the installer (weekly)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 13.1 | One-page report: messaged → replies → booked → attended → won, opt-outs, 1-3 actions | C generates, P sends | `pass_03.../reporting/weekly_client_report.md` | 🛠 script |
| 13.2 | 10-minute call if something is off | P | phone | ✅ |

## Phase 14: End of pilot → keep them

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 14.1 | Pilot review: real numbers for them and for us (fees, time, margin) | C + P | economics sheet | 🛠 |
| 14.2 | Decide: continue / fix / change price / change segment / stop | P | `pass_12.../launch/launch_sequence.md` stage 10 | ✅ |
| 14.3 | Offer next step: the rest of the backlog, then a monthly "we chase every new quote" plan | P | pricing P3 | ✍ |
| 14.4 | Ask for a testimonial / permission to share numbers; ask for 2 referrals | P | email | ✍ |
| 14.5 | Use real results in cold email **only once they exist** | C | experiments | ✍ later |

## Phase 15: Offboarding (if they leave)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 15.1 | Final invoice; return or delete their data as the DPA says | P + C | DPA, Supabase, GHL | 🛠 |
| 15.2 | Close or transfer the GHL sub-account; keep the opt-out list | P | GHL | ✍ |

## Phase 16: Learning loop (every Friday, 30 min)

| # | Action | Who | Tool | Status |
|---|---|---|---|---|
| 16.1 | `results` for each running test; decide using the pre-written rule | P + C | CLI | 🔧 |
| 16.2 | Write the decision in the log; start the next test | P + C | `docs/experiments/LOG.md` | ✅ |
| 16.3 | Update the open questions (backlog size, reactivation rate, price) with new evidence | C | `CURRENT_STATE.md` | ✅ |

---

## What to build next, in the order it's needed

| Needed before | Item | Who | Size |
|---|---|---|---|
| First email | 0.1-0.11 setup | P (C guides) | your time + about 3 weeks warm-up |
| First call | Booking page (0.10); rewrite one-pager + export request (2.6, 3.5) | P, C | small |
| First sample | Audit script + one-page audit report (4.2-4.5) | C | medium |
| First pilot | Pilot agreement + DPA (0.15); intake form (6.1); GHL snapshot: workflow, calendar, pipeline, reply rules (6.2-8.5); homeowner copy (8.1); eligibility + holdout scripts (7.2-7.3) | C (lawyer for the agreement), P for GHL account | large: start at first sample |
| First invoice | Autónomo + NIF, VAT answer, GBP bank (0.12-0.14); billing script (12.1) | P + gestor, C | admin |
| Second client | GHL → Supabase outcome sync (11.2); weekly report script (13.1) | C | medium |

Build in this order and only one milestone ahead. No point building
billing before anyone has replied.
