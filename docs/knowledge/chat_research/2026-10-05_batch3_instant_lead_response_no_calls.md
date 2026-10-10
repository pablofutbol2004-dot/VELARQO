# Batch 3 notes: €1k MRR test, Instant Lead Response, selling without calls

**Source:** ChatGPT chats from batch 3 (AI business tests / Start Business Now / SYSTEM BIZ etc.), saved 2026-10-05 before the chats were removed. These are ChatGPT's claims; I haven't verified the Invoca, FMB, Checkatrade or HighLevel figures.

## €1k/month target: B2B, strongly
- **Filter:** B2B + the pain recurs + the pain has an obvious £ value + AI/software does most of the work + the buyer is cheap to reach. That kills AI summaries, prompt packs, student tools and generic content generators.
- €1k = 4 × €250, 7 × €150 or 10 × €100. Far easier than 100 consumers at €10.
- **Evidence (UK home services):** Invoca 2026 says only 52% of calls are answered by a person and 45% of leads become booked jobs; 53% of consumers expect a reply within an hour, only 33% get one, and 79% would switch to a faster competitor. FMB warns slow replies and poor quote follow-up lose projects. Checkatrade puts the average surveyed home-improvement project at about £11,039.

| Idea | Pain | £ link | Automation | €1k potential |
|---|---|---|---|---|
| Lead/quote recovery | 🔥🔥🔥 | 🔥🔥🔥 | 90%+ | Excellent |
| Missed-call / speed-to-lead | 🔥🔥🔥 | 🔥🔥🔥 | 95% | Excellent |
| Old DB reactivation | 🔥🔥🔥 | 🔥🔥🔥 | 90% | Excellent |
| Tender/opportunity intelligence | 🔥🔥 | 🔥🔥🔥 | 95% | Good |
| Competitor intelligence | 🔥 | 🔥🔥 | 95% | OK |
| Website audits | 🔥 | 🔥🔥 | 98% | OK, as an acquisition product |
| Architecture/student AI | 🔥 | 🔥 | 95% | Meh |
| Generic AI B2C | 🥶 | 🥶 | 99% | Avoid |

- The top three share one infrastructure, an **AI Revenue Recovery Engine**, so test them as different wedges: A speed-to-lead, B **quote recovery** (follow every open quote to a yes, a no or a reason), C database recovery.
- **Bigger product idea: "AI Sales Leakage Monitor".** It connects to the CRM, email, phone, forms and calendar, and sends a morning report like "£38,400 pipeline at risk: 3 enquiries unanswered >30 min, 8 quotes not followed up, 2 cancellations not rebooked…", then acts on it.
- **Content done right:** distribution around one valuable problem ("how UK home-service companies leak revenue"), not becoming a creator. 500 owners of window, kitchen or HVAC companies beat 10k random followers.
- V0 can be GHL + a small backend + an LLM + email/SMS + a simple dashboard, at £100–300/mo. 5 companies × £200 = £1k MRR.

## Pablo's constraints (stated in that chat)
- No GHL yet (too expensive).
- Prefers revenue-tied offers: speed-to-lead, missed calls, website + lead forms. **DB reactivation parked for later.**
- Cold outreach is the acquisition channel.
- Not committed to home services or the UK yet.
- **Doesn't want sales calls.**

## Answer: no sales calls is viable, with a productized offer
Requirements: an obvious demo, obvious ROI, low onboarding friction, and a price low enough to buy without a call.

### First offer: "Instant Lead Response System"
Website enquiry → AI reads it → personal reply in under a minute → 2–4 qualifying questions → booking link, or automated follow-up until a yes or no. The client sees "13 leads → 12 contacted instantly → 8 replied → 5 qualified → 3 booked".
- **Missed-call text-back goes in V2.** It needs phone numbers, an SMS provider, telecom setup, country rules and number forwarding. Web forms are just form → webhook → app → AI → email/SMS → calendar.
- **Stack without GHL** (GHL Starter is about $97/mo): Vercel/Cloudflare, Supabase, Resend/Postmark, Twilio later (pay-as-you-go), Cal.com/Calendly, a cheap LLM, a simple dashboard. **You own the engine**; move to GHL later if needed.

### Niche
The engine is generic, but each campaign must be niche-specific ("Respond to every roofing enquiry instantly before another contractor does").
- **Screen niches on:** high customer value, high cost per lead, speed matters, frequent web enquiries, the owner feels the lost leads, easy to find prospects, can afford £100–300, low regulation, low integration effort.
- **Tier A:** windows/doors, roofing, HVAC/heat pumps, kitchens, remodeling, solar, landscaping/pools, premium trades.
- **Tier B:** aesthetics/med spas, dentists, estate agents, tutoring, professional services.
- **Avoid medical and legal at first** (privacy and compliance).

### Geography
UK first: English, high ticket values, lots of SMBs, GBP, prior research. PECR allows B2B email to Ltd companies (corporate subscribers) with your identity and an opt-out; sole traders and some partnerships count as individuals. Design client forms so they collect proper consent for follow-up.

### Funnel without calls
Cold email → personalized micro-audit or demo → landing page → 60–90 s demo → "try it on your own business" → free or pilot install → results → £149–299/mo.
- **CTA:** "Want me to install a test version on your enquiry form? No call needed." Not "book a discovery call".
- **Example email:** "Noticed your quote form doesn't give prospects an immediate route to book after submitting. I built a system that responds immediately, qualifies and gets suitable leads into your calendar. I can wire a test version to your site so you can see it. No call needed. Worth setting up?"

### Outreach as experiments (50–100 per arm; ignore opens)
1. **Pain:** "you're losing enquiries to slow response" vs "more booked appointments from your existing enquiries".
2. **Offer:** free install vs 14-day pilot vs performance-based first month.
3. **Niche:** windows vs roofing vs HVAC.
- Measure delivery → positive reply → demo accepted → installed → appointment → paid.

### Killer acquisition trick: auto-personalized demos
A crawler reads the prospect's site (name, services, area, form, booking), then the system generates `yourdomain.com/demo/acme-windows` with a simulated conversation ("Looking to replace 6 windows in Leeds" → AI reply). Email: "I mocked this up using your actual website."

### Pricing
- Validation: £99–149/mo.
- Once it's producing appointments: £200–400/mo, or £199 + £X per qualified appointment.
- Rough guess: 500 contacted → 30 interested → 10 pilots → 5 customers.

### Build first
One loop: form → webhook → store → AI interprets → personal reply → booking → follow-up → client sees the outcome. No CRM, DBR, voice, GHL or big dashboard. Build the **acquisition engine** (prospects + auto demos) in parallel. If one niche fails, point both engines at another.
