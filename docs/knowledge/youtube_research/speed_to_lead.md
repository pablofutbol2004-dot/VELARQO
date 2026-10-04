# Speed-to-lead & follow-up: topic digest (59 videos)

- **Source:** ChatGPT's analysis of `velarqo_research/4_speed_to_lead_followup.zip` (2026-10-04), ~1.45M words.
- **Noisy folder:** only ~13 of 59 titles are directly about response, booking, nurture or show rates. The rest is AI-agency, receptionist and GHL content. Concentrated in Adam Erhart 11, Zack Kirk 9, JP Middleton 6 and Michele Torti 5.
- **Verification (Claude, 2026-10-04):** 7 confirmed, 1 misattributed, 1 not found.
  - **JP Middleton's "Harvard" stat is wrong, and inconsistent between his own videos.** In one: "Harvard… 2018… not following up within 5 minutes, your chances… drop by over 400%" [PfhikUzfjDg]. In another it's a "Harvard study… 2017 across over 1,000 brick-and-mortar businesses" [ioJ0dCbeWTs].
    - The real sources are the 2007 Lead Response Management study (~15k leads, 6 companies). It measured *contact and qualification*, not sales.
    - The other is HBR 2011, "The Short Life of Online Sales Leads": firms that try contact within an hour are far likelier to qualify the lead.
    - **Never repeat "400%" in Velarqo copy.**
  - **Daniel Iles on double dialing:** carriers flag numbers that call too often or with too small a gap. Double dialing is risky because you "can't do anything that's intentionally meant to break through a consumer protection", i.e. Focus mode [JEUmEI4REu0]. His own SDR process still double-dials [o1i_mFCOJZI].
  - **Hoani Taylor:** "Begin with a more proactive cadence, like do five to seven follow-ups." Scale down if ~20% push back. If leads ghost, escalate the medium (voice → video) [L_4_gkx5Cuc].
  - **Charlie Morgan:** asking "when can I reach you" is "too much commitment". Ask "What vehicle do you have?" so they only have to respond [IFLM1LrPNtc].
  - **Daniel Fazio:**
    - "Text before you call", so your name shows up when you ring.
    - Call abandoned applications: contact info given, qualification left unfinished [I9P54WrViXE].
    - ⚠ ChatGPT credited text-before-call to Leon Matschke. The quote is Fazio's. Leon's point is "be human": short, casual texts on the platform people already use [q9nSJP1kmx0, vR7UR7Fsuck].
  - **Zack Kirk:** "You simply cannot start with AI receptionists right now", because owners don't trust the AI, or you [jKarGI5tY7I]. Get your foot in the door with an agent that carries no risk for them [QBflLEesyZU].
  - **Cole Gordon:** have "a physical person with an iPhone… confirm every single appointment", because "nobody responds to automated messages or five digit numbers" [VFpO8wNT4zc].
  - **Not found:** Fazio's "mechanical vs decision-driven no-show" split. The concept is sound but treat it as ChatGPT's framing.

## Core finding
**Intent is perishable,** and the mechanism holds without inflated stats: delay brings distraction, competitors and lost motivation.

W&D sits mid-urgency. It isn't an emergency, but homeowners collect several quotes at once, so **the first installer to acknowledge, understand the project and book the survey gets ahead.** Don't sell it like emergency plumbing.

**Strategic update: reactivation monetizes yesterday's leakage; speed-to-lead and quote follow-up prevent tomorrow's.** The prevention layer is the better *recurring* product. Reactivation becomes the fallback layer that catches whatever still escapes.

## Design principles for the Velarqo system
1. **It's a lifecycle, not an instant SMS:** enquiry → acknowledgement → staff alert → human contact → qualification → survey booked → confirmed → attended → quote → follow-up → won/lost/nurture.
   - Remove human memory as the failure point. Boring automations (new contact → SMS → alert → wait → follow-up) do most of the work.
2. **Automation handles timing; humans handle valuable conversations.** First message: acknowledge plus **one easy question** ("Is this mainly windows, doors or both?"). Never "WHEN CAN YOU BOOK???" from an obvious bot; instant but cheap-feeling hurts the brand.
3. **Multi-channel, restrained cadence.**
   - SMS + call + email (WhatsApp where consented). Text before calling.
   - No double-dial tricks. Start around 5–7 touches and **tune the cadence on UK data**, which needs a UK GDPR/PECR review first. US cadences aren't a compliant UK playbook.
4. **AI classifies and routes** (scope, product, timeframe, location, value → CRM update, branch choice, salesperson alert, suggested reply). Use a **green/amber/red router**:
   - Green, automated: acknowledgement, scheduling, reminders.
   - Amber, AI drafts and a human approves: pricing, technical, finance, competitor questions.
   - Red, human immediately: complaints, legal, warranty, vulnerable customers.
   - Human takeover is the design principle.
5. **No AI receptionist at first.** Use **missed-call text-back** plus **after-hours acknowledgement**. The team keeps working as normal and Velarqo catches what falls through, so there's little implementation risk.
6. **Cohorts, not one sequence.** Treat each stage separately, each with its own KPI:
   - A: fresh inbound
   - B: not yet contacted
   - C: contacted but not booked
   - D: survey booked
   - E: no-show or cancelled
   - F: quote issued
   - G: quote stalled
   - H: dormant
   - I: lost (by reason)
   - J: won (reviews, referrals)
7. **Abandoned intent is hot:** partial forms, an enquiry with no survey booked, an estimator used but never submitted.
8. **Show rate is central** if you're paid per *attended* survey.
   - Confirm immediately after booking, ideally by a human-looking number.
   - Pre-survey nurture: what happens at the survey, a relevant project, proof, financing clarity, an easy reschedule.
   - Reminders fix forgetting. Proof and trust fix "booked 3 installers, you're least convincing".
9. **Stop conditions matter as much as triggers:** "already booked elsewhere", "don't contact me", "call me in January", survey booked, sold. You need one source of truth per lead (owner, stage, last touch, next action) so the AI, salesperson and office don't all hit the homeowner within 3 minutes.
10. **Measure the whole funnel per source and cohort:** leads → contactable → contacted → replied → qualified → booked → confirmed → attended → quoted → sold → gross profit.
    - Optimize *incremental GP / cost*. Every other number is a diagnostic; optimizing one alone (reply, booking or show rate) backfires.
11. **Technical moat: an event/state machine,** not a chatbot. NEW_LEAD → CONTACTING → ENGAGED → QUALIFIED → SURVEY_BOOKED → ATTENDED → QUOTE_SENT → FOLLOWING_UP → WON / NURTURE → DORMANT → REACTIVATED, with timestamps, source, attempts, outcomes, revenue and salesperson.
    - Over 50 clients this becomes **the UK replacement-window response model**: best first channel per source, attempts, timing, quote-chase timing, decay by lead age.

## Positioning & rollout
- **Long-term pitch:** "Velarqo finds where paid enquiries leak from your pipeline and closes the leak." That's revenue diagnostics, with reactivation as one module. Some installers won't leak much (call centre, good CRM), and the diagnostic should say so.
- **Front end stays narrow:** the Dormant Pipeline Recovery Pilot (proof, data access, no interference with live leads, clean incrementality).
- **Natural upsell:** "We recovered X written-off opportunities. Want us to stop new enquiries going cold in the first place?" Still no need to run ads; Velarqo improves every acquisition source they already pay for.
- **Rollout:**
  1. Dormant pilot
  2. Confirmation and show-rate optimization (you're already booking surveys)
  3. Fresh-lead speed and not-yet-contacted recovery
  4. Active quote follow-up
  5. The unified lifecycle engine
- **Value ladder:** Dormant Pipeline Recovery Pilot (performance) → Velarqo Revenue Recovery (monthly, new and stalled leads) → maybe acquisition later.

## Don't trust
Speed multipliers ("400%", "first responder wins 78%"), creators' agency revenue, aggressive US cadences, "AI agent = money", and GHL affiliate tutorials (they earn from your signup).

## Ratings
| Item | Score |
|---|---|
| Quote follow-up (W&D) | 9.5 potential |
| Unified lead-lifecycle data | 9.5 strategic |
| Speed-to-lead inside revenue recovery | 9 |
| Human-assisted AI lifecycle system | 9 |
| Dormant reactivation as wedge | 8.5 |
| Missed-call text-back | 7 (feature, not company) |
| Speed-to-lead as standalone "AI service" | 6 |
| AI receptionist to start | 5 |
