# Agency ops, onboarding & retention: topic digest (67 videos, 33 creators)

- **Source:** ChatGPT's analysis of `velarqo_research/7_agency_ops.zip` (2026-10-04), ~443k words.
- **Bias:** the creator spread is cleaner than #5/#6, but the folder is noisy (~40 generic "case studies", plus some false positives). The useful core is ~20–30 videos.
- **Verification (Claude, 2026-10-04):** 6 confirmed, 1 partial.
  - **Nick Saraev, buyer remorse:** "immediately delivering some sort of return on the person that just spent the money… minimizing their buyer remorse… you can usually massively improve retention" [whXs1RaQIDA].
  - **Nick Saraev, onboarding-call win condition:** "my goal by the end of this call is I want our company to have everything we need so we don't have to bother you or ask for permissions every day for the next week… The biggest issue in the space is logistics. Two-factor auth…" [bMmlCPLDk1c].
  - **Partial:** Saraev's "definition of done" in the transcripts is about briefing AI agents [45K3zHckCnQ], not client scope. The principle still applies to scope.
  - **Noah Haupt:** right after "payment complete" on a live call, he sends the onboarding page ("this is what you need to do before tomorrow") [PdNNCC6wqK4]. In another video: forms → scripts within 3–4 days [ZInH_RIDXQA].
  - **Jeremy Haynes:** "We had 16 new people join… three of those people were wrong… we kicked them out. We refunded them", and he reports ~3–3.5% churn [R_YwdxNxcWI]. That figure is self-reported.
  - **Kai Stone:** "why worrying about churn is stupid". Churn is like losing a Tetris block [Watl5dta40s, v_PW9PBWDJg].
  - **Serge Gatari:** avoid churn by making your cost so small the client doesn't notice you, i.e. build-and-release [0waCGka-JOc].

## Core finding
The main risk isn't whether Claude can build Velarqo. It's whether **"yes" → correct data/access → safe launch → homeowners handled → results measured** can run **without Pablo becoming the human glue.**

**Velarqo only works as a business if every client makes the next one easier.** If client #20 is as hard to onboard as #1, it's a conventional agency with Claude making you faster.

**Retention ≠ keeping everyone.** Retain profitable, good-fit clients who get recurring value. Ending a bad-fit client (garbage data, no follow-up, endless custom work, poor margins) can be healthy.

## Onboarding is delivery
Onboarding solves three problems: **buyer remorse, expectation mismatch, logistics.**

**After "yes" there should be no vacuum.** Payment → onboarding booked immediately → a short form → visible progress. Use concise, real operational updates, never theatre:
> "Dataset received: 4,812 records. 3,190 meet the age/status criteria. Resolving duplicates and sold/active records today. Final eligible cohort before launch."

**Scope document (pilot)**
| Velarqo does | Installer does |
|---|---|
| Import the agreed cohort, normalize and dedupe, apply exclusions | Provide accurate data and access |
| Run the agreed outreach, process replies, qualify | Approve campaign parameters |
| Schedule qualified opportunities, send reminders | Keep appointment capacity; take over when needed |
| Attribute results, report | Attend surveys; update quote/sale outcomes; report cancellations; honour opt-outs |

Without this, performance pricing creates **weaponized ambiguity** at invoice time: late callbacks, missed surveys, a rep marking everything "lost", then "not sure these leads were any good".

**Onboarding call (30–45 min early on, one synchronous call is worth it).** Win condition: *everything needed to prepare the first cohort, with no chasing afterwards.* Cover:
- Who sells, who owns the pipeline, who handles recovered leads
- CRM/export, fields and status conventions, the time period
- Dormancy definition and exclusions
- Calendar and handoff/notifications
- Economics: average job, close rate, GP
- Success measurement, communication channel, timeline

A screen-share beats 10 emails for logins, 2FA, permissions and weird fields. Later, pull from the CRM what it already knows. Over time the call shrinks: by client #20 it should be authenticate → 10 questions → approve the cohort.

**Short pre-call form, not a 73-question Typeform:** company, contact, CRM, rough database size, sales team, calendar, service area, products, job range, how old quotes are handled now.

## Launch safety
- **Launch Readiness gate.** No launch until every box is checked:
  - Data: imported, deduped, statuses mapped
  - Cohort: approved, exclusions applied
  - Messaging: sending identity, copy approved, opt-out tested
  - Handoff: owner, calendar and notifications tested
  - Measurement: attribution agreed, tracking tested
- **Small batch → learn → scale** (e.g. 100–300 records first). If "lost" secretly includes next week's installs, finding out at 100 is annoying; at 8,000 it's catastrophic.
- **Kill switch:** pause immediately on complaints, bugs, the wrong cohort, broken personalization or client capacity disappearing. Operational safety beats autonomy.
- **Frame V1 as a baseline phase.** "The first batch establishes response, qualification and booking baselines for your pipeline; we scale if the economics are good." No invented numbers: promise 30, deliver 19 (which may be excellent) and it reads as failure.

## Communication & reporting
- **Predictable beats frequent:** "update every Friday", reliably. Default to async and **call by exception**: strategic decisions, anomalies, requests, renewal or expansion, major issues. Weekly calls with 10 clients = 5 h/week of overhead.
- **Reports answer business questions:** eligible → reached → replies → interested → qualified → booked → attended → quoted → sold → recovered value, plus one key observation. Make value legible: "14 opportunities recovered from records untouched for a median of X days, worth £Y quoted, Z attended."
- **Results still decide:** good communication can't rescue a service with no economic value. No retention tricks like buzzing notifications.
- **Act for reps, dashboards for managers.** The rep gets "Sarah from last August is interested again, call her". Never add admin work for salespeople, or adoption dies. Map the stakeholders: the owner (sponsor), an ops owner, and the sales users.

## Client fit, scope, leverage
- **Qualification is an ops function too.** Check data readiness, volume, economics, capacity, whether someone actually follows up, management responsiveness, technical compatibility, and whether their service is worth selling. **Reject a £1k client who is really a second job.**
- **Four kinds of churn:** bad voluntary (weak value), preventable operational, economic (ICP problem) and strategic (you fire them, which is healthy). Retention drivers in order: fit > outcome > expectations > experience.
- **Scope creep is your specific danger.** With Claude, every "can you also redo our CRM / chatbot / site / ads?" feels easy. **Rule:** if it isn't required for the promised outcome or reusable across many W&D clients, it's out of scope (decline, or charge separately and on purpose). "Can Claude build it?" is an engineering question; "should Velarqo include it?" is a business question. Set a customization budget, and make exceptions visible and paid.
- **Order:** sell carefully → onboard manually and well → watch for repeated friction → document → automate → delegate. **Don't build customer-success systems before customers** (Kai).
- **Machine-readable SOPs** that become connector logic. Example: "CRM X: Quotes > Lost > Export CSV; fields…; gotchas: 'closed' = won + lost; phones lack country code."
- **Founder-led customer success first** (record and transcribe calls, then turn repeated questions into FAQs, steps into automation, decisions into rules, exceptions into requirements or explicitly unsupported cases).
- **Human attention goes to exceptions:** broken integrations, serious complaints, disputes, strategy, expansion.

## Commercial shape (#1–#7)
- **Path:** land with the dormant pilot → prove value → diagnose live leakage from real data → recurring fresh-lead and quote recovery → appointments/no-shows → reviews and referrals → standardize everything repeated.
- **Expansion moves along the same lifecycle.** Never "would you like SEO / TikTok?"
- **Recurring fees need recurring value.** Pure build-and-release (Serge) gives up the data and the loop.
- **The pilot postmortem doubles as the renewal sales meeting.** Cover what happened, what worked, what failed, what surprised us, what changes, and what became reusable. Then: "here's where your live pipeline still leaks".
- **8 profitable, clean clients > 25 nightmare £300 accounts.** The metric next to MRR is **founder hours per client, falling over time.**

## Ops metrics from day one
- **Sale →** onboarding booked → data received → launch-ready → launched
- **Delivery:** records processed, error rate, manual-intervention rate, launch → first positive reply → first qualified opportunity
- **Client dependency:** response delay, unreported outcomes, missed handoffs
- **Economics:** hours per client, variable cost per client, revenue, contribution margin

**Rule for the first clients: one niche, one entry offer, one core workflow, one standard outcome.**
