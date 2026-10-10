# Compliance notes: can we text and email an installer's old quotes?

For Pablo. Plain English, not legal advice. **Have a UK data protection
lawyer check this before the first live send.** Sources are named so you or
the lawyer can check them: ICO, *Guide to PECR*; ICO, *Guidance on direct
marketing using electronic mail*; ICO, *Legitimate interests* guidance; ICO,
*Controllers and processors* guidance; ICO, *International transfers*
guidance. Points marked **(uncertain)** need the lawyer's answer.

## 1. Two sets of rules apply

- **PECR** (Privacy and Electronic Communications Regulations) decides
  whether a marketing **text or email** to a person may be sent at all.
- **UK GDPR** decides whether we may **use** their personal data (store it,
  sort it, load it into GoHighLevel).

Both must be OK. PECR is the stricter one here.

## 2. PECR: texts and emails to homeowners

Homeowners are individuals. A marketing text or email to an individual needs
either **consent** or the **"soft opt-in"**. Texts count as "electronic mail"
under PECR, so the same rule covers both.

Our follow-up messages promote the installer's products, so treat them as
direct marketing. (It could be argued a follow-up on a quote someone asked
for is not marketing. Don't rely on that. **(uncertain)**)

**The soft opt-in works only if all four are true:**

1. **The installer got the details itself, from the homeowner,** in the
   course of a sale or "negotiations for a sale". ICO guidance gives asking
   for a quote as an example of negotiations. So a homeowner who asked
   the installer for a quote can qualify.
2. **The message is about the installer's own similar products.** Following
   up a windows quote with a windows offer is fine. Selling someone else's
   product is not.
3. **The homeowner was given a simple way to opt out when the details were
   collected.** For example, wording on the website form or said on the phone.
   **This is the weak point for most installers.** The ICO fined a company
   in January 2026 for relying on the soft opt-in without having offered an
   opt-out at collection (as reported by law firm summaries).
4. **Every message offers a free, simple opt-out.** Ours say "Reply STOP to
   opt out" (texts) and include an unsubscribe (email).

Also required by PECR: the sender's identity must be clear. Every message
names the installer.

**Who is the "sender"?** The messages go out in the installer's name, about
the installer's products, from details the installer collected. That's what
makes the soft opt-in available: it belongs only to the business that
collected the details. **Both the business that sends and the business that
"instigates" a message can be liable under PECR.** So the installer is
liable, and we may be too as the one pressing send. That's why the evidence
checks below are real checks, not a tick-box.

**How old is too old?** PECR sets no fixed time limit, but the soft opt-in
rests on what people would reasonably expect. Our 24-month cutoff is our own
rule, not a legal line. **(uncertain)**

**Calls:** we don't make calls. Automated calls need specific consent and
live calls have the TPS rules. Texts are not covered by the TPS.

## 3. UK GDPR: using the data

- **Roles.** The installer is the **controller** (decides why and how). We
  are the **processor** (act only on their instructions). This needs a
  written contract with the Article 28 terms: that's `05`.
- **Lawful basis.** Most likely **legitimate interests**: re-contacting people
  who asked for a quote, about that quote, with an easy opt-out. The
  installer should write a short legitimate interests assessment (purpose,
  necessity, balance). [We could give them a one-page template.]
  The Data (Use and Access) Act 2025 makes direct marketing an example of a
  legitimate interest in the law itself. **(uncertain:** check what is in
  force and that it changes nothing for PECR, which still applies on top.)
- **Privacy notice.** The installer's privacy notice should say they may
  follow up quotes and use service providers to do it. If it doesn't,
  ask the lawyer whether that blocks the campaign. **(uncertain)**
- **Opt-outs are forever.** An objection to marketing must be honoured, and
  the person kept on a suppression list so they're never messaged again.

## 4. What the installer must confirm before launch

Evidence, not just a "yes" (intake form `07`, section 4):

1. How the quotes were collected: website form, phone, email, showroom,
   lead sites. Roughly what share each.
2. A screenshot or copy of the **website form and its wording**, and what
   staff say on the phone about future contact.
3. That an opt-out was offered at collection, and how. **(If not: the soft
   opt-in fails for those records and they need consent. See section 5.)**
4. Their do-not-contact / opt-out list.
5. That the records are their own customers' enquiries, not bought or shared.
6. That their privacy notice covers it (link).

## 5. What makes a list (or part of it) unusable

- **Bought or rented lists.** Never.
- **Data from another company:** a previous business, a franchise or
  group company, a partner. The soft opt-in belongs only to whoever
  collected the details.
- **Lead sites** (Checkatrade, Bark, MyBuilder, Rated People and similar):
  we treat these as **not usable** unless a lawyer says otherwise. The
  details came via the platform and the installer didn't offer its own
  opt-out at collection. **(uncertain: this is the strict reading.)**
- **No opt-out offered at collection** and no consent recorded.
- **Unknown source.** Quarantine it; don't guess.
- **Anyone who opted out**, said "don't contact me", or is on their
  do-not-contact list.
- **Won jobs / current customers** (different purpose, different campaign).

When in doubt, leave it out. The import script (`delivery.pilot import`)
already removes won, opted-out, do-not-contact, no-contact-details and
out-of-area records. It stores the lead source but **doesn't exclude by it
yet**, so remove lead-site and unknown-source records by hand until that
check is built.

## 6. Spain (brief)

The messages go out in a UK company's name to UK homeowners, but the
processor (you) is established in Spain. Questions for the gestor/Spanish
lawyer:
- Does the LSSI (art. 21, commercial communications by email/SMS) apply to
  messages we send for a UK client to UK homeowners? **(uncertain)**
- As an EU-based processor, do EU GDPR processor duties apply on top of UK
  GDPR (records of processing, transfers to GoHighLevel in the USA)?
  **(likely yes; to confirm)**
- Does Velarqo need a UK representative under UK GDPR Article 27?
  **(uncertain)**

This is separate from the LSSI risk you already accepted for your own cold
emails to installers. That decision does not cover homeowner messages.

## 7. Quick rules we follow anyway (our rules, not law)

- Send texts 9am-7pm, Monday to Saturday, never on Sundays or bank holidays.
- Stop the whole sequence the moment someone replies.
- No fake urgency, no discount the installer hasn't approved.
- If someone asks how we got their number, answer honestly (see `08`).
