# DB reactivation research: passes 2 and 3 (operator map, UK compliance, V0 playbook)

**Source:** ChatGPT chat "Research DB Reactivation" (6abeb38a), saved 2026-10-05 before the chat was removed. These are ChatGPT's web research findings. Operator results are **vendor-reported**, and the ICO/Twilio points should be re-checked before relying on them.

## Pass 2: what the winning DBR business is
It isn't "AI texts old leads". It's **database intelligence + compliant reactivation + conversation + fast handoff + attribution.**

### Operator map (who to reverse-engineer)
| Operator | Playbook | Steal |
|---|---|---|
| Robb Bailey | Warm DB → offer → SMS → work the replies by hand → book → referrals | The core economics work even without AI |
| Charlie Morgan | DBR as a fast agency "quick win" | DBR as proof-generation, not the final product |
| Dan Wardrope / Flexxable | Performance DBR; two-step "Prince Charming" hand-raise → AI qualify/book (claims ~300 replies / ~30 bookings per 1,000) → upsell speed-to-lead, voice, reviews | How to package and sell DBR |
| Greg Courtepatte / Modern Operator | "Hand-Raise Test": 300–1,000 leads, clean and segment, small live test, then scale | Pilot method |
| Rees Calder / Levity | UK: data quality, compliance, segment by source/recency/lost reason, 10–21-day sequences, performance pricing | The most useful UK operating framework |
| Paul Meyers / PM Consulting | Contractor DBR: separate campaigns for old quotes, past customers, seasonal work, referrals and cross-sells | Treat each cohort as its own campaign |
| LeadBadger | SMS finds interest, automation stops, a human takes over | You may not need conversational AI in V1 |
| Agency Logics | Segment first by where and how consent was captured | Store compliance provenance as a field |
| OnCue AI | SMS + WhatsApp + email + voice over ~14 days (claims 9–12% booked) | Too complex for V1 |
| Sentinay | First ~250 leads free, then pay per interested lead (claims 2–4% booked) | Risk reversal |
| AudienceIntent | $997 setup + revenue share; attribution agreed before launch | Agree attribution up front |
| ASN Activate (UK) | AI SMS for trades, including glazing (claims ~41% reply) | Proof the UK glazing market buys this |
| DatabaseReactivation.co.uk, DoubleGlazingLeads.co.uk | Direct UK W&D competitors (SMS, old leads, warm transfers) | Study their positioning |

Others: Stakd, ZombieSMS, Doppio, Refresh Agent, OnRise, MediaBloom, Ember Intelligence, Simple Tree, Invincible Media, Leads Up AI, Franquility.

### Three messaging schools
Offer-first (Bailey/Morgan), hand-raise-first (Wardrope, Modern Operator, ASN), and **context / reason-lost first** (Levity, PM, OnCue). **For W&D use context-first.** For example, "quoted £8,600 for 9 windows 7 months ago, survey done, timing was bad" is worth far more than a 2022 brochure download.

### Composite playbook
1. Qualify the client: enough dormant opportunities, a decent ticket, capacity, usable data, and they'll report sales.
2. **Compliance audit before the database audit:** record each record's provenance (source, form, date, opt-out wording, suppression).
3. Don't start with the whole DB. Use the highest-intent cohort (unsold quotes and surveys).
4. Run 200–300 records as the first experiment.
5. One short context-aware opener: "You spoke with [company] about replacing your windows last [period]. Did you ever get that sorted?"
6. Keep AI conservative: classify replies, extract intent, answer whitelisted questions only, ask 1–2 qualifying questions. Pricing, finance, guarantees → human.
7. Positive intent → fast human handoff.
8. Track the full funnel: eligible → attempted → delivered → replied → positive → qualified → booked → held → quoted → sold → cash.
9. Compare cohorts and messages (quote age 30–180d vs 181–365d vs 1–2y, price vs timing objection, opener A vs B).
10. After DBR proves ROI, add the always-on layer: speed-to-lead, quote recovery, missed calls, no-shows, nurture. **That's the real business.**

### Moat
The tech is copyable (HighLevel now does bulk enrollment and Conversation AI booking). The real asset is **reactivation outcome data**: lead age × stage × service × quote value × loss reason × season × opener → P(reply / appointment / sale). That lets you say "contact these 1,860 of your 18,000".

### UK compliance (ICO 2026 guidance, as reported)
- SMS/email to individuals needs consent **or** the full soft opt-in. Asking for a quote can count as "negotiations for a sale", but the company must have collected the details itself, be marketing similar products, have offered an opt-out at collection, and include one in every message.
- **Third-party leads** (Checkatrade, Bark, bought lists) are not soft opt-in. Records with unknown provenance → quarantine.
- **Both the sender and the instigator can be liable under PECR.** Onboarding must gather evidence, not a "client confirms compliant" tick box.
- **Automated marketing calls need specific consent**, so shelve AI voice for V1. Live human calls are a different regime (TPS/CTPS).

### Economics
Twilio UK: about $0.056 per outbound segment, $0.0075 inbound, $2.50/mo per number. SMS cost isn't the bottleneck; bad records and weak opportunities are. Optimize **gross profit recovered per eligible contact.** Plan around **1–3% of eligible contacts booked**, not vendor claims of a 47% reply rate.

### Pricing view
**No pure revenue share at first.** There are too many failure points on the client side: answering, showing up, quoting, closing, honest reporting. Pilots: a small or zero-risk test, then **pay per qualified held appointment.** Move to hybrid or revenue share once attribution is proven.

## Pass 3: October operating model
- **UK glazing is unusually suitable:** the industry already tracks lead → appointment → pitch/measure → quote → sale → survey → install, and glazing CRMs (GlazingCRM) log lost quotes, pitch-and-miss, sources, outcomes and values.

### Cohort priority
1. Quoted, didn't buy
2. Pitched or measured, no sale
3. Booked but no-show or cancelled
4. Qualified enquiry with no appointment
5. Uncontacted fresh leads
6. Past customers
7. Old generic enquiries

### Data model (four groups)
- **Identity**
- **Acquisition + compliance:** source, date, platform, collected directly?, form/version, consent evidence, soft opt-in rationale, opt-outs, suppression.
- **Commercial history:** product, number of windows/doors, size, finance, appointment, pitch outcome, quote value and date, lost reason, rep, notes.
- **Reactivation history:** cohort, campaign, opener, send time, delivery, reply class, intent, qualification answers, booked/held, quote, sale, value, attributed revenue.

A client with 4 years of structured CRM history is a strong ICP signal.

### V1 pilot
- 250–500 records from one cohort (e.g. unsold residential quotes 90–365 days old).
- Two openers split at random:
  - **A:** "Hi {first}, it's {person} from {company}. You spoke with us a while back about replacing your {windows/doors}. Did you ever get that sorted?"
  - **B:** "Hi {first}, {person} here from {company}. We quoted for your {project} last {period} but it never ended up going ahead. Is it still something you're considering?"
- AI does intent classification, extraction, 1–3 questions, and proposes a callback. Technical questions → approved knowledge base. Guarantees and negotiation → human. Angry → suppress immediately.
- **Test an instant callback ("want Sarah to call you now?") against a booked survey** (ASN mechanic).

### Qualified-opportunity definition
Market baseline (Lead Pronto): homeowner, postcode in the service area, scope, property type, timescale, confirmed appointment. Optional: finance, minimum job size, both homeowners present, not listed or conservation.

### Price anchor
Lead Pronto: fresh W&D leads from about £15, qualified booked appointments from about £130 (claims 23% lead → appointment, 12% → sale). So **around £100 per genuinely qualified, confirmed opportunity** is defensible.

### Commercial model to test
- Pilot: first ~250 contacts free or nearly free (Sentinay and Modern Operator do this). Data is worth more than £300.
- Then **A:** per qualified hand-raise or survey opportunity, or **B:** per qualified *attended* appointment (preferred if feasible).

### Put in the contract before launch
- Definitions of a qualified and an invalid appointment.
- Cancellation and no-show rules.
- Excluding opportunities that were already active.
- Attribution window.
- The client's duty to report won/lost and the value.

### Pilot dashboard
Eligible → sent → delivered → replies → positive → qualified → booked → held → requoted → sales → revenue → fee → SMS/AI cost, split by opener.

### Other points
- **First proprietary model** = a table or regression P(sale | cohort, age, value, product, lost reason, opener, month), not a trained AI.
- **Positioning gap:** competitors say "dead leads aren't dead" or "AI wakes your CRM". Nobody presents **full lead-recovery infrastructure built around the glazing sales lifecycle**: old enquiries, abandoned quotes, pitch-and-miss, cancellations, speed-to-lead, missed calls, quote chasing, nurture, cross-sell and attribution.
- **Acquisition:** Bailey offers risk-reversal DBR to local businesses, then upsells nurture. Wardrope shows a live AI demo, then a performance partnership, with DBR as the foot in the door.
- **The demo beats a pretty website:** an outreach line like "I'll run it on 250 eligible records at our cost", plus a landing page with an opportunity calculator and a live SMS demo.
- **Sending setup:** use a **two-way number**, not an alphanumeric sender ID (those can't receive replies). Send as the client's brand ("Sarah from ABC Windows"), not Velarqo.
- Ask early: how much of the CRM was collected directly versus delivered by third parties (Checkatrade, Bark)?

### Build today (Velarqo Reactivate V0)
CSV import, normalize and dedupe, suppression list, compliance eligibility field, cohort rules, Twilio two-way SMS, LLM classifier, simple state machine, human takeover, callback/calendar, event log, a tiny dashboard. No voice, no WhatsApp, no big SaaS UI. Let the first client's messy real export shape the product.

### Offer wording
"Velarqo recovers sales from window and door enquiries you've already paid for. We start with your highest-intent lost opportunities, re-open them by SMS, qualify interested homeowners and hand them back to your sales team as confirmed opportunities. We'll prove it on a small batch before you commit."
