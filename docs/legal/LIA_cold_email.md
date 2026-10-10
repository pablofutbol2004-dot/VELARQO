# Legitimate interests assessment: cold email to UK companies

Draft for Pablo to read, edit and agree before the first send. Follows the
ICO's three-part test (purpose, necessity, balancing). Not legal advice; a
UK lawyer should see it with the pilot agreement and DPA before the first
pilot. Date: 2026-10-10. Controller: Pablo [full legal name], trading as
Velarqo, [address], Spain. Contact: hello@velarqo.com.

## 1. What we do with personal data

- **Who:** owners, directors and managers of UK limited companies and LLPs
  in window/door installation, roofing and (later) other home-improvement
  trades. Never sole traders or ordinary partnerships (PECR treats those as
  individuals; they are excluded in code before any send).
- **What data:** company name, address, company number, the business email
  address published on the company's website or a role address at the
  company domain (info@, sales@), and the names and roles of active
  directors from the Companies House register. Phone numbers are stored
  from public listings but not used for cold contact. No home addresses
  (directors' service addresses only), no special-category data, no
  free-mail (Gmail/Hotmail) addresses: those are excluded as likely
  individual subscribers.
- **Sources:** Companies House (public register, open for reuse), the
  company's own website, OpenStreetMap, Google Places business listings
  (used to find the website).
- **Processing:** storing in our database, scoring for fit, sending up to
  three short plain-text emails over about two weeks introducing the
  service, recording replies and opt-outs, and keeping a permanent
  suppression record for anyone who opts out.

## 2. Purpose test: is there a legitimate interest?

Yes. Velarqo's interest is introducing a relevant business service
(follow-up of a firm's own old quotes) to the businesses most likely to
benefit. Direct marketing is expressly recognised in UK GDPR Recital 47 as
a purpose that may be a legitimate interest. The recipients have an
interest too: the service concerns leads they have already paid for. There
is no benefit to any third party and no wider public benefit claimed.

## 3. Necessity test: is the processing necessary?

Yes, in the sense the ICO uses (a targeted and proportionate way of
achieving the purpose). Alternatives:

- **Consent** is not realistic: we have no prior relationship, so there is
  no channel through which to ask.
- **Advertising or content** reaches these firms far less precisely and is
  not available to a new business without proof.
- **Phone** is more intrusive for the recipient and is not used.
- **Contacting only generic addresses** would avoid personal data entirely
  for some companies, but director names are needed to address the right
  person at firms with no generic inbox, and to avoid emailing people who
  have left. Where a generic address exists, it is preferred.

The data used is the minimum needed: name, role, business email, company
facts. Three emails over two weeks is the smallest sequence that gives a
fair chance of being read; nothing is sent after a reply, an opt-out or a
bounce.

## 4. Balancing test

**Nature of the data.** Business contact data from public registers and the
companies' own websites, published so that people can contact the business.
Low sensitivity. No children, no vulnerable people, no special categories.

**Reasonable expectations.** A director of a limited company whose work
email is published on the company site, or who is listed at Companies
House, would reasonably expect occasional relevant business approaches.
PECR permits unsolicited marketing email to corporate subscribers; the
ICO's B2B guidance says the consent rule for email does not apply to them,
provided we identify ourselves and offer an opt-out. The approach is
limited to the trade the service is built for, so relevance is high.

**Likely impact.** Minor: three short emails, easily ignored or stopped
with a one-word reply. No profiling beyond fit-for-service scoring on
company facts (trade, size, years trading, residential focus). No data
sold or shared with third parties for their marketing.

**Safeguards (all enforced in the sending code, `outreach/send_engine/`):**
- Corporate subscribers only (Ltd/LLP from Companies House); free-mail and
  unmatched addresses excluded.
- Sender identity and a working opt-out line in every email; opt-outs,
  "not interested", bounces and complaints suppressed permanently, by
  address and company domain.
- Any reply stops the sequence. Nothing is sent to the same person twice
  for the same step, and no company is contacted again within 90 days.
- Any complaint, or a bounce rate over 5%, switches all sending off.
- Sends only Monday to Friday, 08:30-17:00 UK time, in plain text, with
  no tracking pixels or links in the first email.
- Privacy notice at velarqo.com/privacy.html explains sources, basis,
  retention (24 months) and rights, including the right to object.
- Data held in a password-protected database on the controller's own
  hardware (and later a European VPS), backed up daily.

**Could the individual object or be harmed?** They can object at any time
and the objection is honoured absolutely. We cannot see a realistic harm
beyond a few seconds of attention.

## 5. Outcome

The processing can rely on legitimate interests (UK GDPR Art. 6(1)(f)),
read with PECR reg. 22 for corporate subscribers. **Conditions:** the
safeguards above stay in place; the full legal identity of the controller
is published on the website before the first send; this assessment is
reviewed after the first 2,000 companies, after any complaint, and when
the ICO publishes its revised direct-marketing guidance following the Data
(Use and Access) Act 2025.

## 6. Open items

- [ ] Full legal name and address inserted above and on the privacy page.
- [ ] Lawyer review together with `docs/delivery/04` and `05` before the
      first pilot.
- [ ] Spanish LSSI art. 21: the founder has decided to accept this risk
      (2026-10-01); it is not cleared by this assessment.

Signed: ____________________ (Pablo), date: ____________
