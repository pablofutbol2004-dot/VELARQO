# Letter test: 50 best-fit window and door installers

Status 2026-10-10: **prepared, not ordered.** Pablo approves the list, the
letter and the printer before anything is sent. Idea from
`docs/PATH_6_MONTHS.md` (cheap, high-friction channel nobody else uses;
Alex M H Smith notes in the knowledge base). Pre-revenue, so the letter
claims no results.

## What exists

| Thing | Where | In git? |
|---|---|---|
| The 50 firms, addresses, directors, merge fields | `data/letters_batch1.csv` | no (data/ is local only) |
| 50 print-ready A4 PDFs + one merged file | `data/letters/batch1/` | no |
| Sample letter (fictitious firm, placeholders) | `docs/letters/sample_letter.pdf` | yes |
| Selection script | `outreach/letters/select_batch.py` | yes |
| Letter text and merge logic | `outreach/letters/letter_text.py` | yes |
| PDF generator (reportlab + qrcode, both free) | `outreach/letters/render_pdf.py` | yes |

Re-run:

```bash
D:/velarqo/.venv/Scripts/python.exe -m outreach.letters.select_batch
```

```bash
D:/velarqo/.venv/Scripts/python.exe -m outreach.letters.render_pdf --date 2026-10-27 --photo brand/pablo.jpg
```

Install once if needed: `pip install -e ".[letters]"`.

## The letter

Placeholders in `{{...}}` are filled by editing `SENDER` in
`outreach/letters/letter_text.py` once the legal name, UK number, legal
address and photo exist. Everything else merges from the CSV row.

```
velarqo                                  Pablo {{SURNAME}}        [photo]
                                         Velarqo
                                         {{UK_NUMBER}}
                                         post@velarqo.com
                                         velarqo.com
                                         27 October 2026
{{Director name}}
{{LEGAL NAME LIMITED}}
{{Registered office, 2-5 lines}}
{{POSTCODE}}

Dear {{First name}},

I've written rather than emailed because I'd rather be the one letter on
your desk than the fortieth email in your inbox.

[Mini-estimate, one of three, built only from public facts:]
  a) Your website says {{Firm}} has been at it since {{year on their site}},
     and Companies House has the limited company from {{incorporation year}}.
  b) Companies House shows {{Firm}} has been going since {{incorporation year}}.
  c) {{Firm}} has been fitting windows and doors for a good while.
[then, by years trading:]
  15+ years: A firm trading that long has probably sent out a few hundred
             quotes that went quiet
  8-14:      ... well over a hundred quotes that went quiet
  5-7:       Even in a few years a firm sends out a lot of quotes that go quiet
: not a no, just nothing. They sit in old files or the job system, and
nobody has the time to go back through them.

That is the only thing I do. I take a firm's old quotes that never turned
into a job, three months to two years old, and get back in touch with each
homeowner by text, in your name. This is the message they would get, word
for word:

    "Hi, it's {{Firm}}. We quoted for your windows a while back. Did you
    ever get that sorted?"

Anyone who says they are still interested goes straight into your diary
for a survey. Anyone who says no is left alone for good. You only pay for
surveys that get booked, and the terms are agreed in writing before
anything starts.

I should be straight with you: Velarqo is new, and you would be one of the
first firms I work with. I run it myself, so you would deal with me, not an
account manager.

Here is a small way to test it. Pick five old quotes, ring me, and read
them to me. Ten minutes. I'll tell you honestly whether they are worth
chasing, and you decide from there. No spreadsheet, nothing to send over.

My number is {{UK_NUMBER}}. If you would rather write, post@velarqo.com
comes straight to me. The code at the bottom opens a short page on how it
works.

Yours sincerely,

Pablo {{SURNAME}}
Velarqo
                                   How it works, two minutes:  [QR]
                                   velarqo.com/windows

Velarqo is run by Pablo {{SURNAME}}, {{LEGAL_ADDRESS}}. If you would rather
not hear from me again, say so by email or phone and I won't write again.
Ref L17.
```

283-300 body words, one A4 page, Georgia 10.5 pt. Checked against the
outreach skill: no results, clients or percentages claimed; no price; the
exact homeowner text; "You only pay for surveys that get booked"; the
five-quotes-on-a-call ask; honest that Velarqo is new; who we are and how
to stop hearing from us. The only numbers are Companies House and
their own website; "a few hundred" is hedged with "probably" and never a
fabricated figure.

## Who gets a letter (selection rule)

From the `outreach_queue` view, which already drops parked sites,
suppliers, commercial-only firms, non-UK, Limited Partnerships, firms not
active at Companies House, insolvency history, and suppressed emails or
domains. Then:

- vertical windows, tier A, residential signal on the site, 5+ years trading;
- Companies House category "Private limited Company" (a corporate
  subscriber, so no sole traders or partnerships);
- a registered office address on the Companies House profile, not marked
  undeliverable or in dispute;
- not in any email campaign (`messages` rows; none exist yet, so this is a
  no-op today and a real exclusion on later runs);
- ranked by address quality first, then priority score, then years trading.

Address quality matters because many registered offices are the
accountant's. Rule: "own" if the registered postcode (or its district)
appears on the firm's website; "agent" if the address reads like an
accountant, chambers, c/o, formation agent or a known virtual office, or
the website's postcodes are all elsewhere; "unknown" if the site shows no
postcode. Letters go to "own" addresses first.

Addressee: the longest-serving active human director from the Companies
House officer list, written "Peter Hargreaves" / "Dear Peter". Falls back to
"The Owner" / "Hello," if none.

Batch 1 summary (run 2026-10-10):

| | |
|---|---|
| Candidates after filters | 1,283 (address own/unknown/agent 467/526/290) |
| Chosen | 50, all "own" address, all with a named director |
| Years trading | 8 to 58, median 24 |
| Priority score | 90 to 100 |
| Accredited (FENSA/Certass etc.) | 50 of 50 |
| Website states an earlier start year | 26 (used in the mini-estimate, see check below) |
| Spread | 40+ towns; no more than 3 per county |

Next batch: raise `--limit` or re-run after batch 1 is logged; the script
skips anyone with a `messages` row. Add a `letters_sent` exclusion once
the first batch is posted (log it in the CSV, or a small table).

## Print and post from Spain: cost and route

Prices seen 2026-10-10. Per one-page A4 colour letter, folded, enveloped,
posted in the UK. Stannp's page I checked myself; Docmail's own price list
was unreachable, so its figures are second-hand.

| Route | Per letter | 50 letters | Lead time | Notes | Source |
|---|---|---|---|---|---|
| **Stannp**, FREE plan, standard (2nd class) post | £0.88 ex VAT | about £44 ex VAT (£53 inc) | printed and mailed next business day, then Royal Mail 2nd class 2-3 working days | no minimum, no monthly fee, prices exclude VAT; 1st class is +£1.36 per item (about £112 for 50); extra page £0.08; upload a PDF per letter or a merge; FREE plan has no API | stannp.com/uk/detailed-pricing |
| Docmail (CFH) pay-as-you-go | about £1.01 + VAT | about £50 ex VAT | next-day despatch with a daily cut-off | no minimum; CSV/Excel merge with `<<field>>` tags; card or BACS; **unverified**: price page refused connections | intelliprint.net comparison page; cfh-docmail-ltd.helpjuice.com |
| Intelliprint (alternative) | £0.84 (2nd) / £1.94 (1st) ex VAT | about £42 ex VAT | same-day print and post | no minimum; Signed For £3.51 (2nd) / £4.34 (1st) | intelliprint.net/pricing |
| Royal Mail Click & Drop | n/a | n/a | n/a | only sells postage labels; it does not print or post letters, so it is not a route | help.parcel.royalmail.com |
| Do it yourself from Spain (Correos, international letter up to 20 g, Europe) | €2.00 | €100 plus paper, envelopes, printing and a trip to the post office | 5-10 working days, unverified | foreign stamp and slower arrival undo the "local, personal" effect | correos.com 2026 tariff note |
| Reference: UK stamps from 7 Apr 2026 | 1st £1.80, 2nd £0.91 | | 1st next working day; 2nd 2-3 working days, now delivered on alternate weekdays | | royalmail.com |

**Recommendation: Stannp, FREE plan, standard (2nd class) post, one PDF per
letter, about £44 + VAT for the batch.** Cheapest verified route, no
account fee, next-day print, UK postmark, and the dashboard takes the PDFs
this repo already generates. Pay the 1st class add-on only if the timing
below slips and the letters must land in the same week as the emails.

Before ordering, ask Stannp support three things (none answered on their
site): can a Spanish sole trader register and how VAT is charged; is a
50-PDF upload fine on the FREE plan; where exactly their window-envelope
address zone sits (our address block is at 25 mm from the left, 45-85 mm
from the top, which matches the common hybrid-mail template, but their
proof will show it).

## Timing

Send the week the first email batch goes out (planned about 25 Oct 2026),
so the same firms can see both. The 50 are not in the email cohort today;
if the cohort builder picks any of them, keep them in both: that overlap
is the point of the test.

| Day | Action |
|---|---|
| Mon 26 Oct | Pablo fills placeholders, re-renders, checks 5 PDFs, approves. Order on Stannp with the letters dated 27 Oct. |
| Tue 27 Oct | Stannp prints and mails. |
| Thu 29 Oct to Mon 2 Nov | Letters land (2nd class). First email to the same firms should go out Tue 27 to Thu 29 Oct. |
| 2 weeks later | Count. No second letter; follow up by email or phone only. |

## How to measure

- **Replies by phone**: the letter is the only place the UK number appears
  with "read me five quotes". Log every call as `source=letter`.
- **Replies by email**: the letter uses `post@velarqo.com`, which nothing
  else uses. One Cloudflare Email Routing rule, post@ to the founder's
  Gmail, takes two minutes (Pablo's to-do). Until it exists, change
  `SENDER["email"]` to hello@ and re-render. The sender's domain tells you
  which firm it was, so no per-letter alias is needed.
- **QR scans**: each QR opens `https://velarqo.com/windows?l=L17` (the
  `?l=` is the letter code; the footer prints the same code as "Ref L17").
  The `/windows` trade page is being built in a sibling session; if it
  lands at another path, change `qr_url` in `select_batch.py` and
  re-render. **The parameter is only counted if the site logs it.**
  Cloudflare's free Web Analytics does not keep query strings, so either
  the trade page sends the `l` value in its own beacon, or treat the QR as
  secondary and rely on replies. Do not add tracking that needs a cookie
  banner.
- Verdict rule, same as email: 50 letters is too few for a rate. What we
  learn is whether one or more owners ring. One call that leads to "read
  me five quotes" pays for the batch many times over; zero after two weeks
  means try the mini-estimate by phone (Smith's other suggestion) before
  spending on letters again.

## Legal, in plain words

- Post to a company's registered office is not electronic marketing, so
  PECR's email rules do not apply. UK GDPR still applies because the letter
  names a director: it is the same legitimate-interests basis as the cold
  emails (`docs/legal/LIA_cold_email.md`), and the LIA should mention post.
  The letter says who we are and how to stop hearing from us, and anyone
  who says so goes on the suppression list for email as well.
- The addresses and director names are public Companies House data used
  for the purpose it is published for (contacting the company).
- The Spanish LSSI question (skill item 1) is about electronic
  communications; post is outside it. Not legal advice; Pablo accepted the
  email risk on 2026-10-01 and the letter is the lower-risk channel of the two.

## Checklist before Pablo orders

1. Fill `SENDER` in `outreach/letters/letter_text.py`: surname, UK number,
   legal address line, photo path. Re-render.
2. Spot-check the 26 rows with `website_established_year` set: open the
   site, confirm it really says that year. If not, blank the cell and
   re-render (the letter then uses the Companies House sentence).
3. Open 5 random addresses on Google Maps: do they look like the firm's
   premises? If an accountant's office slips through, drop the row.
4. Read 3 PDFs aloud. Check the director's name looks right (Companies
   House capitalisation is tidied by code, so odd surnames may need a hand
   fix in the CSV).
5. Create the `post@velarqo.com` route in Cloudflare.
6. Order on Stannp (or send Claude the account login flow to prepare the
   upload). Nothing in this repo sends or orders anything.
