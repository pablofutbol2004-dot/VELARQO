# Brief: find the website and business email of 2,000 UK trade companies (batch 6)

For grokbot or any computer-use agent. Paste everything below the line.

---

You are helping a small UK business find the public website and main
business email of registered UK limited companies: **window/door
installers** and **roofers**. We already hold each company's official
Companies House record (number, registered name, town, postcode). Earlier
automatic searches failed for all of these, so the easy search usually won't
work: use the methods below, in order, until one works.

Everything must be **free and public**. No paid tools, no logins, no
accounts, no CAPTCHAs, no contact forms, no messages to anyone.

## Files

Folder: `D:\velarqo\data\agent_tasks\batch6\`

16 input files, about 125 companies each: `find_websites_batch6_part01.csv`
… `find_websites_batch6_part16.csv`.

Work **one file at a time, in order**. For each, save a result file next to
it with `_result` added: `find_websites_batch6_part01_result.csv`. Save
every ~25 companies so nothing is lost. If you stop, continue from the first
file without a finished `_result` file.

### Columns in the result file

Keep the input columns and fill the empty ones:

`company_number, company_name, town, postcode, trade, website, email,
email_source_url, number_on_site, note`

Then add these four columns at the end:

`method, alt_email, alt_email_source_url, alt_email_kind`

- `method`: which method below found the website (e.g. `M1`, `M4`), or
  `none`.
- `alt_email` / `alt_email_source_url` / `alt_email_kind`: only for an
  email the company published **somewhere other than its own website**
  (see "Where emails may come from"). `alt_email_kind` is one of
  `facebook`, `instagram`, `linkedin`, `google_business`,
  `trade_directory`, `pdf`, `other`.

## Where emails may come from

1. **Best, goes in `email`:** shown on the company's own website (contact
   page, footer, about, privacy policy, terms, quote page, a PDF on their
   site). `email_source_url` = the exact page.
2. **Second best, goes in `alt_email`:** published by the company itself on
   its own official profile: Facebook page "About"/intro, Instagram bio,
   LinkedIn company page, Google Business Profile, its own listing on a
   trade body or manufacturer installer page.
3. **Never:** guessed (`info@` + their domain without seeing it written
   down), from an email-finder tool, from a data broker, from a forum post
   by someone else, or from a page about a different company.

Free-mail addresses (gmail, hotmail, outlook, yahoo, btinternet, sky,
aol, icloud…) are fine to record but we may not use them; still note them.

## The methods (stop at the first that works)

**M1. Plain search.** Search engine: `"<name without Ltd>" <town>`. Then
`"<name without Ltd>" <trade word>` (windows / glazing / roofing). Try
Google, Bing and DuckDuckGo: they give different results.

**M2. Company number search.** Search the company number in quotes, e.g.
`"08501292"`. Many UK sites print it in the footer or privacy policy, so this
finds their site even when the trading name is different. Ignore results
from Companies House, Endole, Bizdb, Find-and-update and other company-data
sites; you want the company's own site.

**M3. Postcode search.** Search `"<postcode>" <trade word>` and
`"<postcode>" "<first word of name>"`. Trading addresses often match the
registered office.

**M4. Trading name hunt.** Small firms trade under a different name.
- Open the company on Companies House (find-and-update.company-information.service.gov.uk,
  search the number) → "Filing history" and "People". Look at **previous
  company names** (search those too) and the **directors' names**.
- Search `"<director full name>" <trade word> <town>` and
  `"<director surname> roofing"` / `"<surname> windows"`.
- If the director runs another company in the same trade (People → the
  director → their other appointments), that company's website often covers
  both.

**M5. Trade bodies and installer finders (to find the website, not the
email).** Search the name on: FENSA "find an installer", Certass, GGF
member directory, NFRC "find a member", CompetentRoofer, TrustMark, Which?
Trusted Traders, Checkatrade, Rated People, MyBuilder, Yell, and
manufacturers' approved-installer lists (Liniar, Eurocell, Rehau, Veka,
Deceuninck, Ultraframe, Guardian, Origin, Smart Systems, Everest-style
"find an installer" pages). These pages often link to the company's own
website: follow the link and use the website. An email shown *by the
company itself* on such a listing can go in `alt_email` (kind
`trade_directory`).

**M6. Social profiles.** Search `<name> <town> facebook`, `instagram`,
`linkedin`. Many small installers only have a Facebook page; its "About"
often lists the website and an email. Website → `website`; email →
`alt_email` (kind `facebook` etc.). Read public pages only; if Facebook
asks you to log in, close the pop-up or skip.

**M7. Google Maps / Business Profile (one lookup only).** Search the name +
town on Google Maps. The listing usually has a "Website" button: use it.
Don't copy reviews, hours or photos.

**M8. Domain guess, then check.** Try typing likely domains in the browser:
`<namewithoutspaces>.co.uk`, `.com`, `<name>-ltd.co.uk`,
`<name>roofing.co.uk`. Only accept one if the site shows the company
number, the registered name, or the matching town/postcode. Never record an
email you didn't see written on it.

**M9. Inside the website: dig for the email.** When you've found the site
but no email is visible:
- check `/contact`, `/contact-us`, `/about`, `/privacy`, `/privacy-policy`,
  `/terms`, the footer, any "Get a quote" page;
- open any PDF on the site (brochures, price lists, guarantees);
- view page source (Ctrl+U) and search for `@` or `mailto:` (emails are
  often hidden in the code);
- if the site only has a contact form, write `only a contact form` in
  `note` and try M6 for an `alt_email`.

**M10. Archived site.** If the website is dead or "coming soon", try
`web.archive.org/web/2025*/<domain>` and look at the latest saved contact
page. An email found there goes in `email` only if the domain is still the
company's; put "from archive" in `note`.

## Is it really this company?

It's theirs if at least one of these is true:
- the site shows the same company number, or
- it shows the registered company name, or
- its address or postcode matches the record, or
- it names the director from Companies House and is in the same town.

Set `number_on_site` = `yes` if the company number appears anywhere on the
site.

Same name, wrong place (e.g. "Apex Roofing" in Leeds when ours is in
Bristol): not theirs. A different trade (bookshop, plumber only): not ours,
write it in `note`.

## Notes column

Short, useful: `no website found`, `facebook only`, `site dead`,
`only a contact form`, `trades as Acme Windows`, `different trade`,
`dissolved/closed`, `email from archive`, `two sites found, kept the one
with the number`.

## Time

About 2-3 minutes per company. Use M1-M3 for everyone first; go deeper
(M4-M10) only when they fail. An empty row is better than a wrong one.

## When you finish (or stop)

Reply with: files done; how many websites, `email`s and `alt_email`s
found; which methods worked most (count per `method`); anything odd.
