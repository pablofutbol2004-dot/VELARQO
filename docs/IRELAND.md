# Ireland: second market, groundwork only (10 Oct 2026)

Status: **prepared, not live.** Nothing has been sent to anyone in Ireland
and the send list (`outreach_queue`) is UK-only by construction. The plan
(docs/PATH_6_MONTHS.md) opens Ireland after the first UK case study, around
February 2027. This file says what exists today, what the law requires,
what is still missing, and whether the numbers justify going.

Research with sources: docs/knowledge/web_research/2026-10-11_ireland.md.

## 1. What's done

| Piece | Where | State |
|---|---|---|
| Register download, free | `prospecting/sourcing/cro_bulk.py download` | CRO open data, CC BY 4.0, daily zip (48 MB), no key. Lives in `data/cro_companies.csv.zip` (gitignored). |
| Trade filter | `cro_bulk.py extract --trade windows\|roofing\|kitchens` | Live companies only (`status = Normal`), corporate types only (LTD, DAC, ULC, PLC); NACE code and/or name pattern, same rules as the UK adapter. |
| Country in the database | migration `20261012020000_country.sql` | `companies.country` ('UK' default, 'IE' for these rows); company-number uniqueness is per country; `outreach_queue` gets `c.country = 'UK'` in its base filter (patched from the live definition so it can't undo other sessions' view changes). UK rows unchanged. |
| UK-only enrichment stays UK-only | `free_facts.py`, `places_sweep.py`, `places_websites.py` | Companies House API and Google Places (30/day cap) never see Irish rows. The website refresh does run on them (useful, free). |
| Scoring | `cro_bulk.py push --trade …` | Same ICPs as the UK (country swapped); NACE stored as its UK SIC equivalent so `sic_code_weights` apply. |
| Loaded | database (10 Oct 2026) | 2,615 Irish rows (`country = 'IE'`): windows 1,525 / roofing 675 / kitchens 415 incl. rejects; 27 already tier A/B with an email after the 200-company finder pass. `outreach_queue` shows 0 of them. Migration `20261012030000_source_records_cro.sql` allows `cro` as a raw-record source. |
| Website finder for .ie | `prospecting/enrichment/domain_finder.py` (`COUNTRY_TLDS`) | Name → `.ie`/`.com` guesses, verified against the page; `cro_bulk.py find-websites --sample N`. |
| Eircodes | `lib/normalization/normalize.py` | Kept as "A92 D720"; UK postcodes untouched. |
| Tests | `test_sourcing_cro.py`, `test_country_guard.py` | 10 offline tests; the guard fails if a later view rewrite drops the UK filter. |

### Counts, CRO file of 10 Oct 2026

Register: 825,177 companies ever; **326,469 live**; NACE code on 64% of
live companies, Eircode on 63%.

| Trade | Candidates (live Ltd/DAC/ULC/PLC) | Of which by NACE alone | By name (+trade NACE) | Right trade after scoring (tier C: no email yet) | Rejected by scoring |
|---|---|---|---|---|---|
| Windows/doors/glazing | 1,525 | 1,112 (4332 joinery 734, 1623 carpentry 208, 4752 glass retail 122, 2512 metal doors 48) | 413 | 507 | 1,018 (joinery/carpentry code only: need a website to confirm, as in the UK) |
| Roofing | 675 | 358 (NACE 4391) | 317 | 648 | 27 |
| Kitchens | 415 | 94 (NACE 3102 kitchen furniture) | 321 | 403 | 12 |
| **Total** | **2,615** | | | **1,558** | |

For scale: the UK windows list is 9,981 companies and roofing 18,145 (same
rules), so Ireland is roughly 5% of the UK per trade. Dublin, Cork, Galway,
Meath and Kildare are the biggest counties; 10% of rows have no readable
county.

### Website and email coverage, 200-company sample

Free name-to-domain finder only (`.ie` / `.com` guesses, page must name the
company; a `.com` must also show Ireland, +353, an Eircode or the
company's own town). No Google Places. Random sample of 200 from the 1,558
right-trade companies; one pass, nothing else run yet.

| Trade | Tried | Website found | Email on site | Of those, company domain (not gmail/outlook) |
|---|---|---|---|---|
| Windows/doors/glazing | 72 | 10 (14%) | 8 | n/a |
| Roofing | 76 | 11 (14%) | 10 | n/a |
| Kitchens | 52 | 15 (29%) | 9 | n/a |
| **All** | **200** | **36 (18%)** | **27 (13.5%)** | **16 (8%)** |

Eleven of the 27 emails are free-mail (gmail, outlook): the send engine
refuses those, as in the UK. Sample sizes per trade are small (±10
points). A first run without the `.com` rule found 49 sites, but at least
12 of them were foreign namesakes (a US shingle brand, a Czech company, a
Florida window firm), which is why the rule exists.

For comparison, the UK database today (Companies House rows, after weeks
of finder, website refresh, OSM and Places): windows 4,788 of 12,303 have
a website (39%) and 3,607 an email (29%); roofing 34% and 26%. Irish
numbers after one finder pass are about half of that; the UK number was
reached with more methods, so this is a floor, not a verdict.

## 2. What's legal (S.I. No. 336/2011, reg. 13; sources in the research note)

- **Companies may be emailed until they object** (reg. 13(4): the ban on
  unsolicited marketing email applies to a subscriber "other than a natural
  person" only "where the subscriber or user has notified the person that
  [it] does not consent"). This is the UK PECR corporate-subscriber rule.
- **Sole traders are individuals** (reg. 13(1): consent needed), with one
  Irish extra: reg. 13(2) says email to a natural person at an address that
  "reasonably appears … used mainly … in the context of their commercial
  or official activity", about that activity only, is outside 13(1). We
  don't rely on it: the CRO file contains no sole traders, so none reach
  the list.
- **Generic and named company addresses** are both the company's. There
  is no "info@ only" rule in the text; a named mailbox at the company
  domain is a corporate subscriber's address (and 13(2) covers the person).
  Free-mail addresses (gmail.ie etc.) stay excluded, as in the UK
  (`guards.is_company_mailbox`).
- **Every email must** carry the sender's identity (13(12)(a), no
  disguising) and "a valid address at which that person may be contacted"
  (13(10)(c)) that also works as the address "to which the recipient may
  send a request that such communication shall cease" (13(12)(c)). Our
  signature plus the line *Reply "no" and I won't email again* does both,
  with a postal address added (see 3).
- **Enforcement is criminal, per email.** Each email in breach is a
  separate offence (13(13)); the onus of proving consent is on the sender
  (13(14)); fines up to €5,000 per email summary, €250,000 per email for a
  company on indictment (13(15)). The DPC prosecutes (it did in 2024 for
  emails after an opt-out). Practical rule: the suppression list is the
  whole defence; an opt-out must stop every mailbox and every follow-up
  the same day.
- **GDPR applies to the named contact** exactly as in the UK (13(18) deems
  an email address personal data). The legitimate-interests assessment in
  docs/legal/LIA_cold_email.md covers the reasoning; add an Ireland line
  when we go live.
- **Attribution:** the CRO licence (CC BY 4.0) requires acknowledging the
  source; the adapter prints the line and it goes in any export or client
  report that shows the data.

## 3. What's missing before the first Irish send

1. **Irish-facing identity and postal address in the footer.** Reg.
   13(10)(c)/13(12) require a valid contact address; the UK footer has none
   (name, Velarqo, velarqo.com, the opt-out line). Decide: Velarqo's
   registered address in Spain is lawful but odd for an Irish installer;
   an Irish or UK mailing address (virtual office) is the usual fix. Then
   add it to `compose.SIGNATURE` for country = IE (and arguably UK too).
2. **Free-mail list:** add Irish ISP mailboxes (eircom.net, indigo.ie,
   iol.ie, vodafone.ie, gmail.ie-style) to `guards.FREE_MAIL_DOMAINS` so a
   person's home mailbox is never treated as the company's.
3. **Opt-out wording stays** ("Reply 'no' and I won't email again") and
   must be honoured by `suppressions` for IE rows; verify the reply
   classifier and `send_engine` guards treat IE identically (they do, the
   logic is by email/domain, not country).
4. **Send-engine corporate guard.** `guards.CORPORATE_CATEGORIES` lists UK
   Companies House category strings; CRO types ("LTD - Private Company
   Limited by Shares", DAC, ULC, PLC) are not on it, so the engine refuses
   Irish rows today. Add the four CRO strings when going live; nothing
   else in the engine is UK-specific.
5. **Queue:** `outreach_queue` now has `c.country = 'UK'` in its base
   filter, so Irish rows can never reach it. Going live needs either a
   second view (`outreach_queue_ie`) or a country parameter; the view's
   "uk" page signal needs an Irish twin (+353, Eircode pattern, county
   names, `.ie` domain). Every rewrite of the view must keep the filter;
   `tests/integration/test_country_guard.py` fails if one forgets it.
6. **Email copy:** same text works (English, same trade), but "FENSA /
   Certass" accreditations don't exist in Ireland (NSAI Agrément / SEAI
   grants are the local equivalents); the ICP accreditation regex and any
   copy mentioning them need an Irish variant. Prices in euro.
7. **Time zone:** Europe/Dublin = Europe/London all year (same DST), so
   `guards.SEND_START/END` and `UK = ZoneInfo("Europe/London")` are correct
   for Ireland as they stand; use `Europe/Dublin` by name when the engine
   grows a per-country zone.
8. **Mailboxes:** send from the existing Workspace/M365 mailboxes; no Irish
   domain needed. Warm-up already done. Keep IE volume inside the same
   daily caps.
9. **DPC page read by hand** (the site blocks scripted fetches) and a one-
   paragraph Ireland addendum in the LIA.
10. **Homeowner side (delivery):** Irish homeowners get the same soft-opt-in
   logic (13(11) mirrors PECR reg. 22(3): own similar service, chance to
   object at collection and in every message, **first contact within 12
   months of the sale**, which PECR does not require). The intake audit
   must check quote dates for Irish clients.

## 4. Go / no-go recommendation

**Conditional go: February 2027 as a small second cohort, not a second
growth market.** The legal and build side is ready. The list is smaller
than the UK kill rule (500 companies per offer) needs.

Numbers:

| | Count |
|---|---|
| Live Irish Ltd/DAC/ULC/PLC in windows, roofing, kitchens (name/NACE) | 2,615 |
| Of which right trade after scoring (rest need a website to confirm) | 1,558 |
| Sendable after one free finder pass (company-domain email, 8% of 200) | about 125 |
| Sendable at UK maturity (about 20% company-domain email, same methods) | about 300 |
| UK for scale: windows + roofing + kitchens candidates | 9,981 + 18,145 + 8,827 |

- **Legal:** same rule as the UK for companies. One footer change (a
  postal address) and one guard change. The risk per email is higher
  (criminal, per message) but the controls (suppression list, corporate
  guard, no sole traders) already exist.
- **Size:** about 5% of the UK per trade. Three trades combined give
  roughly 300 sendable companies at maturity, not 500 per trade. That is
  enough to see whether the UK message travels (reply rate, tone), not to
  judge an offer by the kill rule. To reach 500 in one cohort Ireland
  needs more trades (bathrooms, heating, driveways) or a larger NACE
  net (4399 and 4120 hold about 9,800 live companies, mostly builders).
- **Cost:** zero. No key, no paid data, existing mailboxes and tools.

**Do before February (all free, about 2 hours):** push the three
extracts into the database (`push`), run the finder over all 1,558 (about
10 minutes per 200), let the daily website refresh pick them up, then
re-read the sendable count. If it is under 200 after two weeks, treat
Ireland as a message test only and do not spend time on a separate Irish
queue view.

**No-go triggers:** no UK case study by 31 Jan 2027 (decision date 2):
Ireland waits, a second country with no proof doubles the unknowns. Any
sign the DPC reads reg. 13(4) narrower than the statute text (the DPC
page could not be read automatically): stop and take advice.

## 5. How to run it (nothing here sends)

```bash
.venv/Scripts/python.exe -m prospecting.sourcing.cro_bulk download
```
```bash
.venv/Scripts/python.exe -m prospecting.sourcing.cro_bulk extract data/cro_companies.csv.zip --trade windows --output data/cro_ie_windows.csv
```
```bash
.venv/Scripts/python.exe -m prospecting.sourcing.cro_bulk push data/cro_ie_windows.csv --trade windows
```
```bash
.venv/Scripts/python.exe -m prospecting.sourcing.cro_bulk find-websites --sample 200
```

The finder guesses `name.ie` / `name.com`, checks DNS, fetches the page,
and only keeps a site that names the company (and its town for generic
names). Found sites, emails and re-scored tiers are written back to
`companies` (country = IE); the daily website refresh then keeps them
current. Google Places is never used for Ireland.
