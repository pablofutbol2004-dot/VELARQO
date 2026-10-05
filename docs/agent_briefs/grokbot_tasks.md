# Task briefs for Grokbot (computer-use agent)

Paste one brief at a time. Each one is self-contained. Results go back as a
CSV in exactly the format given, saved into `D:\velarqo\data\agent_tasks\`.

Rules for every task:
- Only public pages. Never log into anything, never create accounts, never
  solve CAPTCHAs, never fill in contact forms or send messages.
- Do not bulk-copy Google Maps listings (reviews, ratings, hours, photos).
  Looking up one named business on Google or Maps to find its website is
  fine. Emails only ever come from the business's own website.
  Otherwise use company websites, Companies House
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

---

## Task 3: Find the website and email for registered window companies

**Input:** `D:\velarqo\data\agent_tasks\find_websites_batch1.csv`: 300
UK window/door limited companies (30 per city, 10 cities). We have their
Companies House record but no website. Fill in the empty columns of the same
file and save it as `find_websites_batch1_result.csv`.

**For each row:**
1. Search Google for the company name plus town (drop "Limited"/"Ltd" if
   needed). The trading name can differ from the registered name.
2. Open the website you think is theirs. It counts as theirs only if one of
   these is true: the site shows the same company number, the site shows
   the registered company name, or the address/postcode matches.
3. `website`: the homepage, e.g. `acmewindows.co.uk`.
4. `email`: the main business email shown on that website (contact page,
   footer). Prefer info@/sales@/enquiries@. Never guess an address and
   never take one from a directory.
5. `email_source_url`: the exact page where the email appears.
6. `number_on_site`: `yes` if the company number appears on the site,
   otherwise `no`.
7. `note`: anything odd ("no website found", "only a Facebook page",
   "site says closed", "only a contact form").

Leave website/email empty if you can't find them. An empty row is better
than a wrong one. Spend at most ~2 minutes per company.

**Output:** `D:\velarqo\data\agent_tasks\find_websites_batch1_result.csv`,
same columns as the input:
`company_number,company_name,town,postcode,website,email,email_source_url,number_on_site,note`
