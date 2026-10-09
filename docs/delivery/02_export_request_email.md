# Export request: send right after a good call

Goal: a small sample of old quotes so we can check them (step 4 of
`docs/OPERATING_MAP.md`). Ask for the smallest useful thing. Never ask for
the whole customer list at this stage.

---

Subject: old quotes sample

Hi [name],

Thanks for the chat. As promised, here's what I need to have a look:

A sample of 20-50 quotes from the last 1-2 years that never turned into a
job. A spreadsheet export is perfect. Whatever your system gives you is
fine, I'll sort it out.

The useful columns, if you have them:
- date of the quote
- what it was for (windows, doors, roof, etc.)
- rough value
- status (lost, no reply, went elsewhere...)
- where the enquiry came from (website, phone, Checkatrade...)

You can blank out names, phone numbers and emails for now. I don't need them
to check the list.

Two quick questions as well:
1. Do you keep a list of people who asked not to be contacted? If so, how?
2. Which system are the quotes in (spreadsheet, CRM, quoting software)?

I'll come back within 2 working days with how many look worth chasing.

Pablo
Velarqo, velarqo.com

---

Notes for Pablo
- When the file arrives, save it only under `clients/<company>/` (git
  ignores that folder). Never email it on, never put it in `data/` or git.
- Log it: `python -m pipelines.outbound outcome <email> sample_received`.
- Start the GoHighLevel trial now (see `docs/OPERATING_MAP.md` step 4.1).
- Why blank names are fine: the first check only needs dates, products,
  values and statuses. Personal details come later, under a signed data
  processing agreement.
