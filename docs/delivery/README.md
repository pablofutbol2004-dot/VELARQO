# Delivery: what happens after an installer says yes

Everything here is client-facing or handles client data. Order = the order a
client hits it. Status: ✅ done · 🛠 to build. Step numbers match
`docs/OPERATING_MAP.md`.

| # | Piece | Map step | Status |
|---|---|---|---|
| 1 | "Send me info" reply | 2.6 | ✅ `01_send_info_email.md` |
| 2 | Old-quotes sample request | 3.5 | ✅ `02_export_request_email.md` |
| 3 | Client folder + sample intake (outside git) | 4.2 | 🛠 |
| 4 | Sample check script: column mapping, counts by age/product/status, eligibility (won, opt-outs, too recent, too old) | 4.3-4.4 | ✅ `python -m client_onboarding.sample_audit` (area + data-source checks still to add) |
| 5 | One-page audit result for the installer | 4.5 | 🛠 |
| 6 | Pilot agreement: what counts as a booked survey, no-show credit, cap, weekly invoice, holdout | 5.1 | 🛠 draft, lawyer checks |
| 7 | Data processing agreement (they control the data, we process it) | 5.2 | 🛠 draft, lawyer checks |
| 8 | Intake form: area, products, survey slots, who replies, sender name, data source + opt-out list | 5.3, 6.1 | 🛠 |
| 9 | Holdout split (10-20% not contacted) + stable homeowner IDs | 7.3-7.4 | 🛠 |
| 10 | Homeowner messages (3 texts + email, from the installer's name), approval sheet | 8.1, 6.5 | 🛠 |
| 11 | GoHighLevel campaign: send → stop on reply → STOP opt-out → booking → reminders | 8.2-8.5 | 🛠 (GHL trial starts at first sample) |
| 12 | Outcomes back into our database, weekly report, invoice | 11-13 | 🛠 |

Rules for anything in this folder:
- House style (see `.claude/skills/velarqo-outreach`): plain, short, no
  claimed results, no price in writing.
- Client homeowner data lives only in `clients/<company>/` (gitignored),
  never in `data/` or git.
