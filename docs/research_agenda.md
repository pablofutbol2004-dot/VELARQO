# Velarqo research agenda

Everything we need to know to go from zero to £100k/month as a solo
operator, as concrete questions. `docs/business_map.md` is the overview;
this is the working list.

**How to use it**
- Each question has a **priority**: **P0** = needed before the first
  client, **P1** = needed to reach ~£30k/month, **P2** = needed for scale.
- **Side**: **V** = Velarqo winning clients, **C** = delivering for clients
  (see CLAUDE.md; never mix them).
- **Answered** = a sourced answer written into `truth/` (facts and
  decisions) or `docs/playbooks/` (how-to), with the date. Put the path
  next to the question when done.
- **Sources** tell us where to look. Prefer, in order: our own data and
  experiments > people in the industry > practitioners with public results
  > courses/books > opinion. Record the source for every answer.
- Anything we can measure ourselves beats anything we can read. Where a
  question can be answered by an experiment, the experiment is listed.

**What we already know (2026-09-30)**
- Niche: UK window & door installers, homeowner-facing. 1,918 in
  `outreach_queue`, 792 wave-1 (homeowner-facing, priority 70+).
- Offer (draft): follow-up campaigns on old quotes, performance-based,
  "nothing to pay unless it works". Price, result definition, terms: unknown.
- Cold email: allowed to the UK PECR standard (owner decision, LSSI risk
  accepted). Send gate + footer built; sender identity still TODO.
- Owner based in Spain, entity type unknown.

---

## Part 1: Market

### 1.1 Market size and shape (V)
- **P0** How many UK window/door installers exist in total, and how many are the right size (enough quote volume, owner still decides)? We have 1,918 with email; what share of the real market is that? *Sources: our Companies House + OSM universe, GGF/FENSA published figures, Glass Times / Insight Data market reports.*
- **P1** How is the market split: replacement vs new-build, homeowner vs trade/commercial, uPVC vs aluminium vs timber, by region?
- **P1** Is the market growing or shrinking? Effect of interest rates, housing transactions, energy prices (glazing demand rises with energy costs), the Future Homes Standard, grant schemes (ECO4, Great British Insulation Scheme)?
- **P2** How concentrated is it: how much do the big nationals (Anglian, Everest, Safestyle, Zenith) take vs independents? What happened to Safestyle (administration) and who absorbed its customers?

### 1.2 Next niches (V)
- **P1** Which other trades share the pattern that makes our offer work: many quotes, low close rate, high job value, long consideration, homeowner buyer? Candidates: kitchens, bathrooms, roofing, conservatories/orangeries, solar + batteries, heat pumps, driveways, landscaping, garage conversions, loft conversions, extensions/builders, flooring, stairlifts, home security, EV chargers, fitted wardrobes, garden rooms.
- **P1** For each: typical job value, quote volume per firm, close rate, number of UK firms, how data-ready they are (use CRMs/quoting software?), regulation affecting their customer contact.
- **P2** Does the same pipeline (OSM + Companies House + website) source them well? Test on one before committing.
- **P2** One niche deep vs several niches: at what revenue does a second niche beat going deeper?

### 1.3 Competitors and alternatives (V)
- **P0** Who else offers database reactivation / old-quote follow-up / appointment setting to UK trades? Names, prices, guarantees, positioning, reviews. *Sources: Google "database reactivation UK", "appointment setting for window companies", GHL agency listings, Facebook groups for installers, LinkedIn.*
- **P0** What do installers use instead: doing nothing, the office manager ringing round, their CRM's automated follow-up, lead-gen sites, canvassers, telesales agencies?
- **P1** Lead-gen competitors and their prices per lead: Checkatrade, MyBuilder, Bark, Rated People, Quotatis, Window Quote sites, Facebook lead agencies. What does a fresh lead cost an installer, and how good is it? This anchors our price.
- **P1** What does the "9-word email"/database reactivation agency model look like in the US/UK, and why do those agencies fail or churn?
- **P2** Could a competitor copy us easily? What would make us hard to copy (data, results, niche reputation, process)?

---

## Part 2: The customer (UK installers)

### 2.1 Their sales process (V, and it shapes C)
- **P0** Step by step: enquiry source → first contact → survey visit → quote → follow-up → decision. Who does each step?
- **P0** Typical numbers per firm per month: enquiries, surveys, quotes sent, jobs won. Close rate from quote to sale (hypothesis: 20-35%). Average job value (hypothesis: £3k-£15k).
- **P0** How long does a homeowner take to decide? How long does an old quote stay "alive"? Is a 2-year-old quote worth chasing? A 5-year-old one?
- **P0** Why do quotes die? Price, timing, bought elsewhere, never followed up, partner said no, finance refused, project postponed. Rough split?
- **P1** How many follow-ups does a typical installer do after sending a quote? (Hypothesis: 0-2.)
- **P1** Do they sell on the first visit ("sit and close") or send quotes and wait? The big nationals do the first; independents mostly the second. Affects the size of the backlog.
- **P1** Role of finance offers, price guarantees, seasonal promotions in closing.
- *Experiment: 10 short calls with installers (or a survey in an installer Facebook group) asking these directly. Record answers in `truth/velarqo/customer_research.yaml`.*

### 2.2 Where their data lives (C, decides feasibility)
- **P0** Where are old quotes stored: paper, Excel/Google Sheets, email inbox, quoting software, CRM?
- **P0** Which quoting/CRM software do UK installers use, and can data be exported: Pro-Quote, Business Ecosystem (BE), Easy Job, Glasstech, Evolve, WindowPlus, Fenestration Software, Quotey, Commusoft, Tradify, ServiceM8, Jobber, Pipedrive, HubSpot, spreadsheets? Export format and effort for each.
- **P0** What fields do they have per quote: name, phone, email, address, date, products, price, status, notes? Often phone but no email?
- **P1** If data is only on paper or in an inbox: can we still deliver (manual extraction, a VA, OCR)? At what cost?
- **P1** How many old quotes does a typical firm have (hypothesis: 500-5,000)?

### 2.3 What they buy and why (V)
- **P0** What they currently spend on getting work: lead sites, ads, canvassing, showrooms, trade shows. Monthly budget.
- **P0** What a booked survey is worth to them (job value × close rate × margin), so we know what we can charge.
- **P0** Top objections and past burns: "tried agencies", "leads were rubbish", "my data's a mess", "I don't want to annoy old customers", "GDPR", "I'm too busy", "sounds too good".
- **P1** Buying triggers: quiet month, lost a salesperson, new showroom, cash flow, seasonal dip.
- **P1** Who decides and who influences: owner, co-owner/spouse, office manager, sales manager. How to reach the owner.
- **P1** Language and culture: how they talk (words to use and avoid), what they read, where they hang out (Facebook groups, trade press, forums, trade shows like FIT Show).
- **P2** Their margins and cash position; what financial pressure looks like.

### 2.4 Seasonality (V + C)
- **P0** Which months are busy (spring/summer?) vs quiet (winter?). When are they most open to buying a service? When do homeowners buy windows?
- **P1** Does reactivation work better at certain times (January "new year projects", before winter, energy bill spikes)?

---

## Part 3: The offer

### 3.1 What exactly we sell (V)
- **P0** The core deliverable, in one sentence a window owner understands.
- **P0** What we do vs what the client does: who writes the messages, who sends them, who answers replies, who books surveys, who does the survey.
- **P0** Done-for-you vs done-with-you vs software. Which is easiest to sell first, and which scales to £100k solo?
- **P1** What comes after the old list is used up: ongoing follow-up of every new quote, review requests, referral campaigns, past-customer upsells (doors after windows, conservatory roofs), maintenance/servicing reminders.

### 3.2 Result and pricing model (V)
- **P0** What result do we charge for: reply, booked survey, attended survey, quote sent, sale, revenue won? Trade-offs: easy to prove vs aligned with their profit vs dispute risk.
- **P0** Pricing options and their maths: (a) pure performance per booked survey, (b) setup fee + performance, (c) monthly retainer, (d) retainer + bonus, (e) % of revenue won. Which gets to £100k with least risk and fewest disputes?
- **P0** What do comparable services charge in the UK (per appointment, per lead, retainers)? *Sources: competitor pages, agency forums, asking installers what they pay per lead.*
- **P0** Price per result that is a no-brainer for them and profitable for us: model it from job value, close rate and our delivery cost.
- **P1** Minimum commitment, contract length, cancellation terms.
- **P1** When and how to raise prices; grandfathering first clients.
- **P2** Tiered packages (e.g. reactivation only / reactivation + ongoing follow-up / full sales follow-up system).

### 3.3 Risk reversal and guarantee (V)
- **P0** A guarantee we can honour: "nothing to pay unless it works" (define "works"), "X surveys or you don't pay", pay-on-results only.
- **P0** What if the client doesn't follow up leads we book, or the homeowner no-shows? How do terms protect us?
- **P1** How to stop bad-fit clients: minimum list size, data quality, response-time commitment.

### 3.4 First step / lead magnet (V)
- **P0** A small free or cheap first step that proves value: "send us your old quotes, we'll show you how many are recoverable", a free pilot on 100 quotes, a recorded audit of their follow-up.
- **P1** Does a free pilot attract the wrong clients or delay revenue? What converts pilots into paid?

---

## Part 4: Getting clients (outbound)

### 4.1 Cold email copy (V)
- **P0** What works on UK trade owners: length, tone (casual/direct), plain text vs formatting, spelling (British English), no jargon ("database reactivation" means nothing to them).
- **P0** Subject lines that get opened by a busy owner, including lowercase/short/company-name styles.
- **P0** First lines: which personalisation is real and valuable vs creepy/fake? What true data we have: years trading, town, FENSA/Certass, services on their site, reviews.
- **P0** The call to action: ask for a call, ask a question, offer a free audit, ask for permission to send info. Which gets more positive replies?
- **P0** Proof without case studies: how to be credible with zero clients (honest framing, the mechanism, a pilot offer).
- **P0** Follow-ups: how many (3? 5?), gaps between them, what each one adds (new angle, maths, social proof, break-up).
- **P1** Replying: templates for "how much?", "send info", "not interested", "who are you?", "how did you get my email?", "remove me", out-of-office.
- **P1** Personalisation at scale: when AI-written first lines help and when they hurt.
- *Experiment: A/B test 2-3 openers and 2 CTAs on wave 1 in batches of ~100; track positive reply rate per variant (the experiment tables already exist).*

### 4.2 Deliverability (V)
- **P0** Separate sending domain(s) so the main velarqo domain is never at risk. How many domains/inboxes for our volume?
- **P0** SPF, DKIM, DMARC, custom tracking domain or none; plain text; no open-tracking pixels; links or no links in email 1.
- **P0** Warm-up: needed? how long? tools?
- **P0** Safe volume per inbox per day (hypothesis: 30-50) and ramp schedule.
- **P0** Google Workspace vs Microsoft 365 inboxes; which lands better with UK trade inboxes (many use Outlook/365, BT, gmail).
- **P0** Bounce handling: verify emails before sending? which verifier? What bounce rate is dangerous (hypothesis: >2%)?
- **P1** Sending tools: our own Gmail/Outlook API sender vs Instantly / Smartlead / lemlist. Cost, deliverability, inbox rotation, reply detection. Build or buy?
- **P1** Spam complaint rate thresholds (Google/Yahoo 2024 bulk sender rules: <0.3%) and how to stay far below.
- **P1** Monitoring: Google Postmaster Tools, blacklist checks, seed tests.

### 4.3 Lead data quality (V)
- **P0** Decision-maker first names: Companies House officers (directors) as a proxy for the owner; accuracy for small firms.
- **P0** Email accuracy: generic inbox vs named; how often info@ reaches the owner in a small firm.
- **P1** Refresh cadence: companies close, emails change; re-enrich every N months.
- **P1** Paid data worth buying? (Apollo, Lusha, Cognism, UK trade directories.) Compare to our free universe.
- **P2** Signals of "in pain now": hiring salespeople, reviews mentioning slow response, recent ads, seasonal dips.

### 4.4 Other outbound channels (V)
- **P1** Cold calling UK businesses: rules (TPS/CTPS screening; PECR allows B2B calls unless registered), best times, scripts, from Spain (UK number, call recording rules).
- **P1** LinkedIn: are window firm owners on it? Connection + message sequences; limits.
- **P1** Direct mail / letters to owners: cost, response rate, pairs well with email.
- **P1** Personalised Loom/video: worth it for top-priority leads?
- **P2** Facebook groups for installers, trade forums, WhatsApp groups.
- **P2** Trade shows (FIT Show, regional events) and trade press.

### 4.5 Outbound benchmarks (V)
- **P0** What are realistic numbers per 1,000 emails sent: delivered, replies, positive replies, calls booked, clients won? *Sources: our own experiment data first; published cold email benchmarks second.*
- **P0** How many leads do we need to hit 1, 5, 20 clients? We have 1,918 ranked + more if other niches.

---

## Part 5: Trust, inbound and partnerships

### 5.1 Proof (V)
- **P0** How to get the first case study: free/discounted pilot, what to measure, permission to publish, format (numbers + quote + name).
- **P1** What proof convinces installers most: £ recovered, surveys booked, a named local firm, a video testimonial?

### 5.2 Referrals and partners (V)
- **P1** Fabricators and suppliers who sell to hundreds of installers: would they refer/co-sell? (A fabricator's revenue grows when its installers win more jobs.)
- **P1** Trade bodies and schemes (FENSA, Certass, GGF, TrustMark): partnership or advertising options?
- **P1** Software vendors (quoting/CRM tools): integration or referral partnerships?
- **P1** Client-to-client referrals: incentive that works.

### 5.3 Brand and content (V)
- **P1** Website/landing page: what an installer needs to see (clear offer, how it works, proof, who's behind it, UK contact).
- **P2** Content that earns trust with installers: LinkedIn posts, YouTube breakdowns ("how many surveys are hiding in your old quotes"), a calculator tool.
- **P2** Positioning a Spain-based operator for UK clients: UK phone number, UK company or address, honesty about location.

---

## Part 6: Sales

### 6.1 The call (V)
- **P0** Discovery call structure (15-30 min): their numbers, their data, their pain, fit check, next step.
- **P0** Qualifying questions and disqualifiers.
- **P0** Showing value on the call: back-of-envelope maths with their own numbers.
- **P1** Closing: asking for the pilot/contract on the call, handling "I need to think about it", "talk to my partner".
- **P1** Objection library with best answers (trust, price, GDPR, "customers will be annoyed", "my data's a mess", "tried agencies").

### 6.2 From yes to live (V + C)
- **P0** Proposal and contract in one simple document; e-signature.
- **P0** Onboarding checklist: data export, consent confirmation, DPA, GHL/sending setup, offer to homeowners, calendar access, who answers replies.
- **P0** Time from yes to first messages sent (target: under 7 days).

---

## Part 7: Delivery: reactivation campaigns (C)

### 7.1 Campaign design
- **P0** Email vs SMS vs both for homeowners. SMS in the UK: reply rates, costs, sender ID rules, consent.
- **P0** Message sequences that bring old quotes back: short, personal, from the installer (owner name), low-pressure question ("are you still looking at new windows?"). The "9-word email" pattern and its variants.
- **P0** Offers to homeowners that are real and honest (DMCC Act 2024): price-match, updated quote, free re-survey, finance, seasonal install slot, loyalty discount. Which the client can actually honour.
- **P0** Segment-specific messages: lost on price, went quiet, no-show, bought elsewhere (ask for referral/review), quote expired.
- **P1** Timing: day/time for homeowners; gaps between messages; how many touches before stopping.
- **P1** Handling replies: who answers, how fast, scripts to book the survey.

### 7.2 Results to expect
- **P0** Realistic reply and booking rates from old quotes, by quote age (hypothesis: 5-15% reply, 2-5% booked). *Sources: our first pilots; published DBR case studies (discount heavily).*
- **P1** How results decay with quote age and with repeated campaigns.

### 7.3 Speed to lead and booking
- **P0** Why speed matters (reply within minutes) and how to guarantee it: we answer and book, AI assistant, or the client's office.
- **P1** Booking flow: calendar links vs calls; reminders to cut no-shows; confirmation messages.

### 7.4 After the old list
- **P1** Ongoing product: automatic follow-up of every new quote, review requests after installs, referral asks, annual check-ins. This is what makes clients stay.

---

## Part 8: Delivery: tools and data (C)

### 8.1 GoHighLevel
- **P0** Agency plan needed; sub-account per client; cost per client.
- **P0** Snapshots: one reactivation snapshot we install per client.
- **P0** SMS in the UK via GHL (LC Phone / Twilio): alphanumeric sender IDs, costs, opt-out handling, deliverability.
- **P0** Email from GHL in the client's name: sending domain per client, authentication.
- **P1** Workflows: reply detection, booking, reminders, pipeline stages, reporting.
- **P1** AI features (conversation AI) for replying to homeowners: quality, risks.
- *Existing: `docs/ghl/` has the docs pack; `integrations/ghl/` has the sync.*

### 8.2 Client data handling
- **P0** Import and cleaning of messy exports (our `client_onboarding/` + `database_reactivation/` pipelines).
- **P0** Consent/soft opt-in check per client list and per contact; what to exclude.
- **P1** Dedupe against the client's current customers and recent contacts; suppression lists per client.
- **P1** Data retention and deletion when a client leaves.

---

## Part 9: Results, attribution and billing (V + C)

- **P0** How to prove a booked survey came from our campaign (GHL source, booking link, CRM stage), so billing is never disputed.
- **P0** Client report: what they want to see weekly (messages sent, replies, surveys booked, quotes, jobs won, £).
- **P0** Invoicing and payment: Stripe/GoCardless direct debit, invoice terms, VAT treatment (not subject to Spanish VAT, art 69 LIVA).
- **P1** Tracking "revenue won" if we charge on sales: client honesty, verification.
- **P1** Per-client economics: time spent, SMS/tool costs, margin.

---

## Part 10: Retention and expansion (V + C)

- **P1** Why clients leave in this model (list exhausted, results drop, they stop answering leads) and how to prevent each.
- **P1** Monthly value that justifies staying after month 1-2.
- **P1** Expansion: more products per client, more locations, related trades they know.
- **P2** Lifetime value and churn targets for £100k/month maths.

---

## Part 11: Legal and compliance

### 11.1 Business setup in Spain (V)
- **P0** Autónomo vs SL for this business: tax at £5k, £30k, £100k/month; liability; admin cost; how UK clients perceive each.
- **P0** Registration steps (Modelo 036/037, IAE epigraph, RETA), social security costs (cuota, tarifa plana).
- **P0** Invoicing UK clients: not subject to Spanish VAT (art 69 LIVA), Modelo 303 reporting, VeriFactu from 2027.
- **P1** Income tax (IRPF) brackets vs corporate tax (IS) at each revenue stage; when to switch to an SL.
- **P1** Beckham law / non-habitual regimes: relevant or not?
- **P2** A UK Ltd as well? Pros, cons, tax residency and "place of effective management" traps.

### 11.2 Our outreach (V)
- **P0** PECR B2B rules in practice: corporate vs individual subscribers, identification, opt-out. Already in `truth/compliance/uk.yaml`.
- **P1** LSSI risk (accepted): what enforcement actually looks like for small senders; how complaints arise; examples. *Owner asked for examples.*
- **P1** UK GDPR for prospect data: legitimate interests assessment, privacy notice, UK representative (Art 27).
- **P1** Cold calling rules if we add phone.

### 11.3 Client campaigns (C)
- **P0** Emailing/texting a client's past quote recipients: soft opt-in (did they "negotiate for a sale"? a quote counts?) vs consent; ICO guidance on old customer lists.
- **P0** Our role as processor; data processing agreement template (UK GDPR Art 28).
- **P1** DMCC Act 2024: honest offers, no fake urgency, no fake discounts.
- **P1** SMS-specific rules (PECR applies to SMS equally).

### 11.4 Contracts (V)
- **P0** Service agreement for performance deals: definition of a result, billing, disputes, termination, liability cap, data terms.
- **P1** Terms of our guarantee, written so it's honourable and not exploitable.
- **P1** Insurance: professional indemnity, cyber.

---

## Part 12: Money

- **P0** Unit economics per client: price, delivery costs (GHL, SMS, tools, our time), gross margin.
- **P0** Cash flow on performance deals: costs we carry before we get paid; how long.
- **P1** Cost to acquire a client (tools, domains, data, our time) and payback period.
- **P1** Financial model: clients × price × retention → months to £30k and £100k.
- **P1** Tools budget by stage; what's worth paying for.
- **P2** Personal: taxes, savings, reinvestment, runway.

---

## Part 13: Systems and automation (V)

- **P1** What to automate first to stay solo at 20-40 clients: lead sourcing (done), scoring (done), outreach sending, reply triage, call booking, onboarding, campaign setup (GHL snapshot), reporting, invoicing.
- **P1** One dashboard: pipeline (leads → replies → calls → clients), each client's results, cash.
- **P1** SOPs for every repeated task so a VA/contractor can take it later.
- **P2** AI agents for reply handling (ours and clients'), with guardrails.

---

## Part 14: Scaling solo (V)

- **P1** Which tasks go to software, freelancers/VAs, or stay with the owner (sales calls, key relationships, offer decisions).
- **P1** Productising: identical offer, setup, messages and report for every client in a niche.
- **P2** When to add niche 2, a second offer, or a partner.
- **P2** Capacity maths: hours per client per week at 20 and 40 clients.

---

## Part 15: The owner (V)

- **P0** Weekly rhythm: outreach blocks, calls, delivery, review.
- **P0** The five numbers to check every week (e.g. emails sent, positive replies, calls held, clients won, £ billed).
- **P1** What not to do at each stage (e.g. no second niche before 5 happy clients; no content before case studies).
- **P1** Working UK hours from Spain (1 hour ahead); availability for calls.

---

## Sources to use (breadth, not one guru)

- **Our own data**: experiment tables, Supabase, pilots. The most trustworthy source.
- **Installers themselves**: calls, surveys, Facebook groups for UK window/door installers, trade forums.
- **UK trade**: GGF, FENSA, Certass, Glass Times, Glazing Summit, Insight Data, FIT Show.
- **Regulators**: ICO (PECR, UK GDPR), AEPD and BOE (LSSI, LOPDGDD), HMRC, Agencia Tributaria, legislation.gov.uk.
- **Offer and sales**: Alex Hormozi ($100M Offers / Leads), Chris Voss (negotiation), Jeb Blount (prospecting), SPIN Selling, The Mom Test (customer interviews).
- **Cold email practitioners** with public results: Instantly/Smartlead/lemlist research and benchmarks, practitioners who publish reply data.
- **Database reactivation**: GHL agency community, published DBR case studies (treat claimed numbers sceptically).
- **Deliverability**: Google and Yahoo sender guidelines, Google Postmaster Tools docs, M3AAWG.

## Top 12 to answer first (P0 that unblock sending and selling)

1. The result we charge for and the price (3.2).
2. The guarantee and its terms (3.3).
3. The free first step / pilot (3.4).
4. What an installer's old-quote backlog looks like: size, age, where it lives, export (2.1, 2.2).
5. What a booked survey is worth to them and what they pay per lead today (2.3, 1.3).
6. Cold email: opener, CTA, follow-up sequence (4.1).
7. Deliverability setup: domains, inboxes, volume, warm-up (4.2).
8. Director first names for the queue (4.3).
9. Discovery call script + objection answers (6.1).
10. Onboarding checklist + contract + DPA (6.2, 11.3, 11.4).
11. The homeowner reactivation sequence we'll run for client 1 (7.1).
12. Autónomo vs SL and invoicing UK clients (11.1).
