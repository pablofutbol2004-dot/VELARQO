---
name: velarqo-outreach
description: Velarqo's house rules for anything a prospect or client will read - cold emails, follow-ups, replies, website copy, one-pagers. Use whenever writing or reviewing outreach copy, choosing who to contact, or planning a send, together with the generic cold-email/copywriting skills. Holds the offer facts, voice, honesty limits, and the legal checklist that must pass before anything is sent.
---

# Velarqo outreach rules

These override generic copywriting advice when they conflict. Product truth lives in `PRODUCT.md` at the repo root; read it first.

## The offer (only say what is true)

- Velarqo runs follow-up campaigns on a firm's old, unconverted quotes and books a share of those homeowners back in as appointments.
- Performance-based: "You only pay for surveys that get booked" (billing unit decided 2026-10-04). Cold test arm B offers to chase a firm's first 50 old quotes free. Terms agreed before anything starts.
- Never write "nothing to pay unless it works" or "pay only if it works". It is misleading: they pay per booked survey even if no sale follows.
- **No price in marketing copy or emails.** Never state a price, per-survey fee, or percentage in cold emails, replies in writing, or website copy. The price is tested on calls and lives in the signed agreement and invoices only. This rule is about marketing and emails, not contracts or invoices, which must state the price.
- Verticals: UK window and door installers (ICP in `config/templates/icp-template.json`) and domestic roofing (`cold_roofing_v1`). Default offer line lives in `outreach/personalization/generator.py` (`DEFAULT_OFFER_LINE`).
- Old quotes we work: 3-24 months old, not won, not opted out.

## Honesty limits (hard rules)

- Pre-revenue, zero clients. Never claim or imply results, clients, case studies, "we've helped", percentages, or years of experience.
- Never invent urgency, scarcity, or fake personalisation ("saw your recent post" when we didn't).
- Personalisation must come from real data in the lead record (company name, town, trade, website fact). If a field is missing, drop the sentence rather than fudge it.

## Voice

- British English spelling. Plain, short sentences. Sounds like one person writing to another tradesperson, not a marketing team.
- Use their words: quotes, surveys, fitters, diary, jobs, homeowners. Avoid: leverage, solutions, AI-powered, growth, pipeline, funnel, synergy, "I hope this finds you well".
- Cold emails: under 80 words including signature and opt-out (enforced in `compose.problems`), one idea, one soft ask (a reply), no links or attachments in the first touch, plain text.
- Sign-off: Pablo, Velarqo, velarqo.com. Every email says who we are and how to opt out ("Reply 'no' and I won't email again").
- Greet the owner by first name when the company has exactly one active director (Companies House). Otherwise a plain "Hi,". Never "Hi there" or "Dear Sir/Madam".
- Never lead with or mention "AI", "automation" or "software" to prospects: owners suspect AI marketing bots and won't log in to tools. Say what a person does for them ("I chase them", "in your name").
- No revenue promises, money-back bravado or big round numbers ("30 sales in 30 days"); owners read them as scams. Small and believable beats bold.
- Their control, stated: their name, their customers, they approve every word, homeowners who say no are left alone.
- Any statistic used must name its source in plain words ("a survey of 140 tradespeople"). Learnings and sourced lines: `docs/LEARNINGS.md`, `docs/NICHE_PROFILE.md`.

## Homeowner-facing messages (sent in the installer's name)

- Calm, plain British, short: the tone of "No rush", "No bother". The double-glazing pressure-sales reputation is the thing to be the opposite of.
- No deadlines, no "today only", no discount offers, no finance figures (a monthly finance figure is a financial promotion: link to the lender's calculator or leave it out).
- When price is the doubt, restate what's included (guarantee, materials, who fits it), never undercut.
- Stop at the first "no". Every message carries a free opt-out ("Reply STOP").
- Send late afternoon or early evening; homeowners reply after work.
- Only to homeowners the installer can lawfully contact (soft opt-in with an opt-out at collection, or consent). See `docs/delivery/06_compliance_notes.md`.

## Legal checklist (run before ANY send)

Status as of 2026-10-01: **founder decision: proceed with cold email to UK corporate subscribers.** Pablo has accepted the Spanish LSSI risk himself (item 1 is not legally cleared, just a risk he has chosen to take). Items 2-4 are enforced in code by the send engine (`outreach/send_engine/`): corporate-only recipients, opt-out line + sender identity on every email, permanent suppression.

1. **Spain (LSSI art. 21)**: the founder operates as an autónomo established in Spain. LSSI art. 21 bans unsolicited commercial email without prior consent, and the AEPD applies it to business recipients (legal persons) too, not only individuals. This directly conflicts with cold email. Needs a Spanish lawyer/gestor's answer on: does it apply to emails sent to UK businesses; would a UK Ltd managed from Spain change it; which channels are safe.
2. **UK PECR**: B2B email to *corporate subscribers* (Ltd companies, LLPs, public bodies) is allowed without consent if we identify ourselves and offer an opt-out. Sole traders and ordinary partnerships count as individuals and need prior consent: exclude them (Companies House-sourced Ltd firms are fine; OSM/website-only firms may be sole traders).
3. **UK GDPR / EU GDPR**: legitimate-interests basis for named directors' work emails, with a documented LIA, privacy notice at velarqo.com/privacy.html, opt-out list honoured forever (suppression list). **Open: no LIA has been written yet.** It must exist before the first send (~25 Oct).
4. Every email: real sender identity, physical/legal identity available on the site, working opt-out. **Open:** the founder's full legal name and address are not on velarqo.com yet; add them before the first cold email.

## Before handing copy back

- Run the `humanizer:humanizer` skill over the draft (removes AI-sounding phrasing), then re-check the rules below: humanizer must not add claims, prices or urgency.
- Check each claim against PRODUCT.md "Evidence on Hand". If it isn't there, cut it.
- Count words; read it aloud as a window fitter would hear it.
- State which checklist items are still open.
