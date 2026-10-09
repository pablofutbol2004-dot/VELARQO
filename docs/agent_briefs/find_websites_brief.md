# Brief: find the website and email of UK trade companies

Works for any agent (grokbot or another computer-use bot) or a human
assistant. Paste everything below the line.

---

You are helping a small UK business find the public website and main
business email of registered limited companies in two trades: **window/door
installers** and **roofers**. We already have each company's official
Companies House record. We need their website and email.

## Files

Folder: `D:\velarqo\data\agent_tasks\batch5\`

16 input files, 125 companies each: `find_websites_batch5_part01.csv` …
`find_websites_batch5_part16.csv`.

Work through them **one file at a time, in order**. For each input file, save
a result file next to it with `_result` added to the name, e.g.
`find_websites_batch5_part01_result.csv`. Save each one as soon as it's done,
so nothing is lost if you stop. If you stop part-way, continue from the first
file that has no `_result` file.

Columns (same in input and result; only fill the empty ones):
`company_number, company_name, town, postcode, trade, website, email, email_source_url, number_on_site, note`

`trade` tells you what kind of firm it is: `windows` or `roofing`.

## For each company

1. Search Google (or another search engine) for the company name plus the
   town. Drop "Limited"/"Ltd" if it helps. The name on their website can
   differ from the registered name. Try once more with the trade word
   ("roofing", "windows") if the first search finds nothing.
2. Open the website you think is theirs. It only counts as theirs if at
   least one of these is true:
   - the site shows the same company number (often in the footer, terms or
     privacy page), or
   - the site shows the registered company name, or
   - the address or postcode on the site matches.
3. `website`: the homepage, e.g. `acmeroofing.co.uk`.
4. `email`: the main business email shown **on that website** (contact page,
   footer, about page). Prefer info@ / sales@ / enquiries@ / office@.
5. `email_source_url`: the exact page where you saw the email.
6. `number_on_site`: `yes` if the company number appears anywhere on the
   site, otherwise `no`.
7. `note`: anything useful, short: "no website found", "only a Facebook
   page", "site says closed", "only a contact form", "different trade
   (bookshop)", "email from search results, not on site: x@y.com".

## Rules

- Only public pages. Never log in, create accounts, solve CAPTCHAs, fill in
  contact forms or send messages.
- Never guess an email (no "probably info@their-domain"). Never take an email
  from a directory, Facebook, Yell, Checkatrade or similar. If the only email
  you can find is outside their own site, put it in `note`, not in `email`.
- Don't bulk-copy Google Maps listings (reviews, ratings, hours, photos).
  Looking up one company to find its website is fine.
- If the company is clearly not in the trade (e.g. a bookshop), leave website
  and email empty and say so in `note`.
- An empty row is better than a wrong one. Spend at most about 2 minutes per
  company, then move on.

## When you finish (or stop)

Reply with: how many files are done, how many websites and emails were found,
and anything odd you noticed.
