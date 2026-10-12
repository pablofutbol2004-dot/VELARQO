# Brief: find the website and email of US home-improvement contractors

For Grokbot (or any computer-use agent, or a human assistant). Paste everything below the line.

---

You're helping a small business find the public website and main business email of licensed US contractors: **kitchen & bath remodelers, window & door companies, roofers, and siding/exterior firms** in Oregon and Washington. We already have each company's official state licence record (name, city, phone). We need their website and email.

## Files

Folder: `D:\velarqo\data\agent_tasks\us_batch1\`

There are 16 input files of 125 companies each, `us_find_part01.csv` to `us_find_part16.csv`.

- Work through them **one file at a time, in order**.
- For each one, save a result file next to it with `_result` added to the name, e.g. `us_find_part01_result.csv`.
- Save each result as soon as it's done. If you stop, continue from the first file that has no `_result` file.

Columns are the same in the input and the result. Only fill the empty ones:
`source_id, company, trade, city, state, zip, phone, owner_name, website, email, email_source_url, google_reviews, note`

## For each company

1. **Search** Google for the company name plus the city and state. Drop "LLC" or "Inc" if that helps. Their website name often differs from the licence name. If nothing turns up, try once more with the trade word ("roofing", "remodeling", "windows").
2. **Confirm the website is theirs.** It only counts if at least one of these is true:
   - the site shows the same phone number (compare digits; the area code may be formatted differently), or
   - the site shows the licence name, or
   - the site shows the same city and clearly the same business.
3. **`website`:** the homepage, e.g. `acmeroofingpdx.com`.
4. **`email`:** the main business email shown **on that website** (contact page, footer, about page). Prefer info@, office@, sales@ or the owner's own address.
5. **`email_source_url`:** the exact page where you saw the email.
6. **`google_reviews`:** if Google shows the business's review count when you search for it, write just that number (e.g. `143`). Leave it empty if it isn't shown. Don't copy reviews or ratings.
7. **`note`:** anything useful, kept short, e.g. "no website found", "only a Facebook page", "site says closed", "only a contact form", "commercial only", or "email seen elsewhere, not on site: x@y.com".

## Rules

- Only public pages. Never log in, create accounts, solve CAPTCHAs, fill in contact forms or send messages.
- Never guess an email (no "probably info@their-domain"). Never take an email from a directory, Facebook, Yelp, Angi, BBB or similar. If the only email is outside their own site, put it in `note`, not in `email`.
- Look up one business at a time. Don't bulk-copy Google Maps listings.
- If you're unsure, leave the cell empty. A blank is better than a wrong answer.
- Don't change the `source_id` column. That's how we match your results back.
