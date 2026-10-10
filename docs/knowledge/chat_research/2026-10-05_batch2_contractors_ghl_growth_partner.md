# Batch 2 notes: selling to contractors, GHL business models, growth-partner principles, solo agency

**Source:** ChatGPT chats from batch 2 (Earning selling to contractors, GHL Business Models, Growth Partner Principles, Business Systems Overview, Agency model overview, and others), saved 2026-10-05 before the chats were removed. These are ChatGPT's claims; I haven't verified the Jobber, ServiceTitan or HighLevel points.

## Selling to contractors (Earning selling to contractors)
- **The best offer is revenue recovery + lead conversion, not marketing:** "You already paid for leads. I make sure more of them turn into booked jobs."
- **Evidence:**
  - Jobber 2026: 70%+ of customers expect a same-day reply and over half expect one within an hour, but only 20% of contractors reply within an hour.
  - ServiceTitan: among $10M+ contractors, nearly half say estimate follow-up brings in 11–15% of revenue.
- **System:**
  1. Old-database reactivation (old enquiries, lost quotes, "not ready", no-shows, past customers due for service).
  2. Speed-to-lead.
  3. Missed-call recovery.
  4. **Unsold-estimate follow-up**, maybe the most valuable piece: day 1, day 3 (objection/question), day 7, day 14 (financing or availability angle), day 30, then nurture.
  5. Reviews, referrals and repeat jobs.
- **Niches:**
  - Best: roofing, windows & doors, HVAC replacement, kitchen/bath remodeling, solar/insulation.
  - Mid: plumbing/electrical and landscaping.
  - Handyman is too low-ticket.
- **Target:** £500k–£10M revenue (thousands of contacts, salespeople, CRM, ad spend), not one-man trades.
- **Pricing:**
  - First: £500–1,000 setup + £X per qualified appointment, or £0–500 + % of attributable revenue.
  - Once proven: £1.5–3k/mo + a performance component.
  - The pitch: "Don't trust us. Let the first campaign make you money."
- **Expansion:** DBR → unsold estimates → speed-to-lead → missed calls → qualification/booking → CRM pipeline → reviews/referrals → lead gen → full revenue system.
- **Ranking of agency offers:** revenue recovery > booked-job lead gen > Google Ads/LSA > CRM automation > AI receptionist > SEO/GBP > websites > social > generic "AI automation".
- **Positioning:** "Velarqo, revenue infrastructure for home-improvement companies." Wedge: recover revenue from old leads and unsold quotes for UK W&D companies. Get 5–10 undeniable case studies first.

## GHL business models (GHL Business Models)
- **Rule:** don't sell GHL. Sell an economic outcome where GHL quietly does 80–95% of fulfilment (white-label SaaS, snapshots, rebilling of AI and other add-ons).
- **Ranking:**
  1. Vertical Revenue OS
  2. AI receptionist/setter
  3. Lead-conversion system
  4. DBR
  5. Missed-call recovery
  6. Niche SaaS
  7. Reputation
  8. AI DM/webchat setter
  9. No-show/recall
  10. Website-as-a-service
  11. CRM setup agency
  12. Snapshot/template business
- **Models people miss:**
  - **Middleware SaaS:** leave the client's CRM alone and connect it to GHL as the comms/automation engine (LeadEngage with Follow Up Boss: $149–297/mo, about 300 customers).
  - **AI resale:** sell Voice/Conversation AI as your own product.
- **Vertical Revenue OS example:** "ClinicOS" at €499/mo plus €500–1,500 setup. 50 clinics = about €25k MRR on one cloned snapshot.
- **Recall systems** (dentist 6-month clean, Botox at 4–6 months, garage MOT at 11 months) are underrated and sticky.
- **Website-as-a-service:** "websites for roofers £199/mo" with forms, chat, CRM, booking, SMS, reviews and missed calls.
- **For Pablo:**
  1. Velarqo DBR → Revenue Recovery / Lead Conversion OS.
  2. AI receptionist + missed calls.
  3. Vertical SaaS + managed service (€399/mo software + €500–2k/mo service).
  4. AI inbound setter.
  5. Pure GHL SaaS later.
  - Velarqo is the outcome company, and GHL is the invisible operating system underneath.

## Is GHL dumb or smart? (DB reactivation architecture)
- GHL in 2026 has an AI Decision Maker (branching), AI Agent workflow actions, intent detection/extraction/summaries, Conversation AI booking, and AI-built workflows.
- **Architecture:** **outside GHL** = business brain (Python + Claude: DB analysis, cleaning, cohorts, scoring, campaign strategy, experiments, cross-client learning, compliance). **Inside GHL** = operational brain (Decision Maker, Conversation AI, Agent) + deterministic workflows (SMS/email/wait/DND, booking, pipeline).
- **Example cohorts:**
  - A: recent unclosed quotes <12 months, >£5k
  - B: enquired but never quoted, <6 months
  - C: old lost quotes, 12–36 months, high value
  - D: past customers for cross-sell
  - X: do not contact
- **Intelligence levels:**
  1. Deterministic (opt-out → stop): workflow.
  2. Classification: GHL intent detection.
  3. Conversation: Conversation AI.
  4. Operational next step: GHL Agent / Decision Maker.
  5. Business reasoning (which of 14k to target, ROI, lessons): outside GHL.
- **Own the logic** (scoring, segmentation, benchmarks, attribution, cross-client data) so GHL stays replaceable (HubSpot, ServiceTitan, Jobber later). Premium GHL AI actions cost per run, so use Python for the 45k easy records and AI only where there's real uncertainty.

## Growth-partner principles (Growth Partner Principles: a 10-hour growth-operator course transcript)
- Don't copy his full-stack creator rev-share model (team of 7, ads, webinars). Steal the principles:
  1. Client selection beats marketing.
  2. Diagnose before prescribing.
  3. Demonstrated proof before earned proof (audits, teardowns, mystery shops, calculators, 1–2 free implementations).
  4. Research customers from their actual language (voice notes, sales calls, Reddit).
  5. Map each problem to a concrete deliverable; value also comes from speed, risk reduction and done-for-you.
  6. **Only use performance pricing when you control the outcome.**
  7. Feed delivery data back into marketing.
- **Ladder:** audit → single intervention → system/product → recurring optimization → growth partnership. KLEOS/TALOS engines (Data, Choices, Business) already match this.
- Suggested follow-up: extract it into `growth_operator_playbook.md` (STEAL / ADAPT / IGNORE / TEST).

## Business systems map (Business Systems Overview)
- A business is a set of systems moving info, money, customers and work: lead gen, capture, CRM, qualification, pipeline, DM/email/WhatsApp automation, calls, booking, quoting, payments, onboarding, operations, inventory, customer comms, support, retention, reactivation, upsell, referral, reputation, content, analytics, finance, HR, SOPs and management.
- **Sell the fixes to broken connections between systems**, not software. Example: Instagram → WhatsApp → manual reply → customer lost becomes IG → DM → qualify → CRM → appointment → reminder → job → payment → review → maintenance reminder → reactivation.
- **Automotive priorities:** lead capture + CRM, WhatsApp/phone, booking, quote follow-up, missed calls, reminders, job status, reviews, service/MOT reminders, reactivation, referrals, owner KPI dashboard.

## Keys for a solo agency / growth partner
- Optimize **monthly gross profit per hour of your own time.**
1. Sell a narrow promise, even with broad knowledge.
2. Diagnose broadly, intervene selectively.
3. Productize the process: intake → analysis → diagnosis → prioritization → intervention → measurement → review.
4. Async by default.
5. Use AI for cognition (analysis, audits, diagnosis, reporting, QA), not just content.
6. Standardize inputs (data schemas; know what's missing).
7. Build an intervention library: problem → conditions → signals → intervention → data → KPI → failure modes.
8. Automate stable work, not chaos (do it manually first).
9. Brutal scope boundaries (own / influence / client-owned).
10. Choose clients for operational compatibility.
11. Track leading indicators: leads → response → bookings → shows → closes → AOV → repeat → revenue.
12. Avoid rev-share early.
13. Design for exceptions.
14. Have a hard capacity model.
15. Retain by finding the next constraint.
16. Only build software that cuts marginal work.
17. Keep human judgment at the high-value layer.
