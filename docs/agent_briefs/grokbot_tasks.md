# Task briefs for Grokbot (computer-use agent)

Paste one brief at a time. Each one is self-contained. Results go back as a
CSV in exactly the format given, saved into `D:\velarqo\data\agent_tasks\`.

Rules for every task:
- Only public pages. Never log into anything, never create accounts, never
  solve CAPTCHAs, never fill in contact forms or send messages.
- Do not scrape Google Maps. Use company websites, Companies House
  (find-and-update.company-information.service.gov.uk) and the directories
  named in the task.
- If a site's terms forbid copying its listings, note that and skip it.
- If something is unknown, leave the cell empty. Never guess or invent.

---

## Task 1: Quality check of 50 window installers

**Input:** `D:\velarqo\data\agent_tasks\spotcheck_50.csv` (50 UK companies
with name, Companies House number, website, town, email).

**For each row, find out:**
1. Is the website live and is it this company? (yes / no / no_website)
2. Do they install windows/doors **for homeowners** (not trade-only, not
   commercial-only, not just a supplier)? (yes / no / unclear)
3. Are they still trading? Check Companies House status (active / dissolved /
   liquidation) and whether the site looks maintained.
4. Rough size: number of staff or vans if stated, or "one-man band" / "small
   team" / "large" from the site.
5. Owner or director name: from the site's About page, else the first active
   director on Companies House.
6. A named email for that person if published on their own website (not
   guessed).
7. One-line note on anything odd.

**Output:** `D:\velarqo\data\agent_tasks\spotcheck_50_result.csv` with columns:
`id,company_number,website_ok,homeowner_installer,trading_status,size,owner_name,owner_email,owner_email_source_url,note`

---

## Task 2: Where to find the next trades

Velarqo will add three more UK trades: **conservatories/orangeries**,
**roofing (domestic)** and **fitted kitchens**. We need lists of UK
businesses for each.

**For each trade, find:**
1. Public directories or registers of UK businesses in that trade (trade
   associations, competent-person schemes, accreditation bodies, council
   approved-trader schemes), e.g. for roofing: NFRC, CompetentRoofer;
   for kitchens: KBSA; for conservatories: CERTASS, FENSA, GGF.
2. For each source: URL, roughly how many UK members it lists, whether the
   listing shows website / email / phone, and whether its terms of use allow
   reuse (quote the relevant line, or "not stated").
3. The UK SIC codes that best match the trade (Companies House codes).

**Output:** `D:\velarqo\data\agent_tasks\trade_sources.csv` with columns:
`trade,source_name,url,approx_uk_listings,shows_website,shows_email,shows_phone,terms_allow_reuse,terms_quote,notes`
plus a short `trade_sic_codes.txt` listing SIC code, description and trade.
