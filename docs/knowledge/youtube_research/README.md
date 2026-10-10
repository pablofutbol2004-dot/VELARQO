# YouTube research digests (copied 2026-10-04)

These are verified digests from the YouTube library in `D:\KNOWLEDGE_BASE`: about 13.3k videos and 13k transcripts. ChatGPT analysed topic zips of transcripts. Claude then checked the key claims against the transcripts and saved the result. Each file lists which claims were **confirmed, corrected or not found**, with `[video_id@mm:ss]` sources.

**The source of truth is `D:\KNOWLEDGE_BASE\digests\`.** If a digest changes there, it gets copied here again. Treat these as hypotheses: real installer calls and pilot data outrank them, the same rule as the rest of `docs/knowledge/`.

## Index
| File | Use it for |
|---|---|
| `home_services.md` | How home-service businesses leak demand; W&D specifics; ICP (good/avoid); "revenue recovery" positioning |
| `sales_closing.md` | Founder calls for the first 5–10 clients; discovery questions; the Fazio "it's my leads anyway" objection and the fix (written-off dormant cohort + holdout) |
| `offers_pricing.md` | Billable event (qualified *attended* survey); small credited deposit vs free; max two charging mechanisms; guarantees only after 5–10 campaigns |
| `speed_to_lead.md` | The recurring product after the pilot: speed-to-lead, missed-call text-back, quote follow-up, show rate; lifecycle state machine; the "400%" stat is wrong |
| `ghl_infrastructure.md` | Architecture: own the intelligence layer, buy the rails, never force a CRM migration; V1 = CSV + human; 12 acceptance criteria |
| `reviews_referrals.md` | Post-sale loop: neutral review requests, referral engine; **no review gating, no incentives** (Google policy + UK DMCC Act) |
| `agency_ops.md` | Onboarding win condition, scope split (us vs installer), launch-readiness gate, small batch + kill switch, ops qualification, scope creep |
| `meta_ads_local.md` | Paid acquisition later: measure downstream (cost per attended survey), Google vs Meta, creative = persona×angle×offer, Ad Library as research, capacity-aware demand; Meta not for acquiring installers yet |
| `cold_outreach.md` | Cold email mechanics and offer-first outreach |
| `content_acquisition.md`, `faceless_content.md` | Content as proof for outbound (later), and its limits for B2B |
| `jp_middleton.md`, `corey_ganim.md`, `taylor_haren.md` | Channel digests: the reactivation agency model, diagnosis-first offer ladder, experimental outbound (70/20/10) |
| `watch_later_lessons.md` | Running lessons from Watch Later reviews: funnel-by-step tracking, competitor "prospect" calls, kill criteria, security pass before client data, execution rules |

## Digging deeper (raw library)
Run these from `D:\KNOWLEDGE_BASE`, with `py` rather than `python`:
```
py -m ytm search "quote follow up" --snippets   # full-text search over titles + transcripts
py -m ytm text <video_id> --timestamps          # read a transcript to check a cited claim
py -m ytm cards <topic>                         # pre-ranked cards, where they exist
```
Topic zips for ChatGPT are in `C:\Users\pablo\Desktop\velarqo_research\` (1–8). All 8 zips are now analysed.

## Conflicts with current repo docs (to reconcile here, not decided yet)
1. **Billable event.** `docs/PRICING.md` P1 bills per *booked* survey, with no-shows credited, and keeps "attended" for P2. `offers_pricing.md` and `speed_to_lead.md` argue for *attended* from the start. Supporting evidence: Noah Haupt bills home services at "150 for each estimate you actually come face to face with + 1k setup" [nyx7OidDjmQ]. P1's no-show credit is close to this already, so the decision is mostly about wording.
2. **Free vs deposit.** `docs/PRICING.md` uses no setup fee and "free first few surveys" as a lever, and `SALES_PLAYBOOK.md` replies say "nothing to pay unless surveys get booked". `offers_pricing.md` recommends a **small activation deposit credited against the first fees**. Supporting evidence: Clay Lawrence's switch to zero-risk pay-per-review brought in "bad customers" and unpredictable revenue [FObpNztnuug]. Possible test: add a "credited deposit" arm to P2.
3. **The written-off cohort and the holdout** (`sales_closing.md`) match `pass_12` (holdout/baseline). There's no conflict; it just strengthens the existing design.
4. **Agreed already, no change needed:** founder calls of 15–20 min, no prices in emails, pricing from the client's economics (the 3 call questions), the monthly retainer as the long-term model, and no guarantees.
5. **Not in the repo yet:** the launch-readiness gate, the kill switch, the scope split with installer responsibilities (`agency_ops.md`), and the review/referral compliance rules (`reviews_referrals.md`).
