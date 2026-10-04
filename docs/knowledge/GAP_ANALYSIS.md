# Pass 14 vs the repo — gap analysis (2026-10-01)

Short version: **finding and qualifying companies is largely built. Sending
safely is not.** Nothing should be sent from code until the "Must fix before
first send" items are done — and the legal question (LSSI art. 21 / UK PECR
route) is answered by a lawyer.

## Already built (Pass 14 stages covered)

| Pass 14 stage | Where in repo |
|---|---|
| Universe discovery | `prospecting/sourcing/` (Companies House, CH bulk, OSM), `pipelines/uk_universe/build.py` |
| Identity / dedupe | `prospecting/deduplication/merge.py`, `lib/scoring/matching.py` |
| Website resolution | `prospecting/enrichment/domain_finder.py`, `website.py` |
| Qualification / scoring | `lib/scoring/icp_score.py`, ICP version stored (`data/supabase_store.py:icp_version`) |
| Provenance & history | `source_records`, `website_snapshots`, `score_history`, `events` tables |
| Idempotent loads | `data/supabase_store.py` push is re-runnable |
| Suppression table | `public.suppressions` (email + domain, reasons incl. unsubscribed/bounced) |
| Variant tracking | `lib/tracking/experiments.py`, `messages` table |
| Send channel | `integrations/email/` (Gmail + Outlook) |

> **Update 2026-10-01:** items 1-6 below are built in `outreach/send_engine/`
> + `pipelines/outbound/` (migration `20261001000000_send_engine.sql`).
> Item 7 is a DNS task in `docs/LAUNCH.md`. Founder accepted the LSSI risk;
> email is the channel.

## Must fix before first send (critical gate items)

`integrations/email/sender.py` sends every item in a queue with no checks.

1. **Suppression recheck at send time** (AF15, OR06) — sender never looks at
   `suppressions`. Check email *and* domain immediately before each send.
2. **No double-send** (AF16, AF17) — no idempotency key per
   (campaign, contact, step); a re-run would email everyone again. Also skip
   anyone already in an active conversation.
3. **Kill switch** (AF18, OR17) — no way to pause a campaign mid-run, and no
   automatic stop on a bounce/complaint spike.
4. **Opt-out → suppression** (AF22, OR15) — `classify_reply` recognises
   "unsubscribe"/"remove me", but `handle_reply` only records sentiment; it
   never writes to `suppressions`.
5. **Opt-out line in every email** (AF13) — check templates include one.
6. **Human review queue** (AF23, OR16) — complaints / legal-sounding replies
   must go to a person, not an auto-route.
7. **Sender domain setup** (AF19, OR01) — SPF/DKIM/DMARC on a separate
   sending domain, not velarqo's main one. Done in DNS, not code.

## Should do, not blocking a small manual first cohort

- Decision-maker resolution with role confidence (AF07) — today contacts are
  mostly generic/role inboxes from websites; fine for a first cohort.
- Email verification adapter + accept-all policy (AF09, AF10).
- Compliance route per contact: incorporated company vs sole trader /
  partnership (AF11, OR08) — UK PECR treats these differently. Companies House
  match already tells us "Ltd" vs not; store it as an explicit route field.
- Inbound reply ingestion wired to a real mailbox (AF21).
- Funnel join company → reply → call → export → pilot (AF26).

## Not needed yet

Provider-agnostic adapter framework, enrichment job queue, VPS deployment,
cohort freezing machinery. Revisit after the first 10 installer conversations.

## Recommended order

1. Lawyer answer on cold email (blocks everything email-related).
2. Meanwhile: phone / LinkedIn outreach to installers using
   `pass_13_first_10_installers/sales/20_min_installer_call.md` — no code needed.
3. Fix items 1–6 above (small: one send-guard module + reply→suppression).
4. First cohort of ~20–30, manually inspected (OR19).
