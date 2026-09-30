# Research first pass (2026-09-30)

Desk research on the P0 questions in `docs/research_agenda.md` that don't
need the owner. Meant to be **contrasted** with the owner's expert material
and, above all, with our own results. Confidence: **High** = official source
or consistent across many sources; **Med** = several practitioner sources
agree; **Low** = single/vendor source, treat as a guess.

---

## 1. What a booked survey is worth to an installer (agenda 2.1, 2.3, 3.2)

| Fact | Value | Conf. | Source |
|---|---|---|---|
| Whole-house uPVC replacement, 3-bed semi | £4k-£12k (commonly £4.5k-£9k) | Med | [bookabuilderuk](https://www.bookabuilderuk.com/blog/window-replacement-cost-2026), [MyBuilder](https://www.mybuilder.com/windows-door-fitting/price-guides/window-replacement-cost), [Checkatrade](https://www.checkatrade.com/blog/cost-guides/double-glazing-cost/) |
| Price per uPVC window, supply + fit | £300-£750 | Med | same |
| Price spread between firms for the same spec | 30-50% | Low | [Checkatrade](https://www.checkatrade.com/blog/cost-guides/double-glazing-cost/) |
| In-home sales close rate (home improvement, mostly US data) | ~25-35%; 27% often quoted as benchmark | Med | [Hook Agency](https://hookagency.com/blog/contractor-good-closing-rate/), [Leap](https://leaptodigital.com/blog/one-call-close/) |
| Share of in-home sales closed on the first visit | ~70% | Low | [No Smoke and Mirrors](https://www.nosmokeandmirrors.com/2025/03/31/the-power-of-the-one-call-close-in-b2c-in-home-sales/) |
| Chance of closing drops on a second appointment | up to -50% | Low | same |

**What it means.** Rough value of one booked survey to an installer:
£7k job × ~27% close ≈ **£1,900 of revenue**, maybe £600-£800 gross profit.
A survey from an *old* quote probably converts below 27% (the homeowner
already said no once), so discount it. Hypothesis to test: 10-20%.

**Contrast with:** owner's material on pricing; installer interviews (what
they actually close from old quotes).

## 2. What installers already pay for leads (agenda 1.3, 2.3)

| Source | Cost | Conf. |
|---|---|---|
| Checkatrade | from £59/month (12-month contract); members report £80-£500/month; lead fees £5-£40 | Med |
| MyBuilder | no monthly fee; £5-£35 per shortlist | Med |
| Bark | £1.80/credit; £5-£40+ per lead | Med |
| Dedicated window lead sellers | £10-£70+ per lead (e.g. Lead Pronto from £15) | Med |

Sources: [LocalAdder tracker](https://localadder.co.uk/uk-trade-lead-cost-tracker/), [Whito](https://whito.co.uk/research/uk-trade-directory-costs/), [LocalSearchNorth](https://localsearchnorth.uk/blog/checkatrade-vs-bark-vs-mybuilder/), [Lead Pronto](https://leadpronto.co.uk/window-door-double-glazing-leads/).

**What it means.** A *lead* is cheap (£5-£70) but shared, cold and often
lost; a *booked survey* is worth far more. Our pricing anchor should be
"cost per booked survey", not "cost per lead". Hypothesis: installers
effectively pay £100-£300 per survey through lead sites once you account
for lead-to-survey conversion. **Unverified; ask installers.**

## 3. Competitors: UK database reactivation (agenda 1.3)

| Provider | Model | Price | Channels |
|---|---|---|---|
| Vantage Growth Partners | flat monthly | £297 / £497+ per month | SMS + email + booking/reviews |
| Invincible Media | tiered monthly | £197-£797/month + setup | SMS, WhatsApp, email, DMs |
| ASN Activate | performance (negotiated) | not published; 200+ contact minimum | AI SMS |
| Bigfoot Agency | pay on results | not published | conversational AI via GHL |

Source: [Vantage's comparison page](https://www.vantagegrowthptnrs.com/database-reactivation-uk-compared) (written by a competitor, so biased), [SalesHandy agency list](https://www.saleshandy.com/agencies/pay-per-appointment/united-kingdom/).

**What it means.**
- The space exists, but it's generalist ("any business with a list"),
  cheap-subscription or vague "pay on results". Nobody we found is
  **niche-specific to window installers** with a defined per-survey price.
  That's our positioning gap.
- Monthly subscriptions of £200-£800 set a price ceiling in buyers' heads
  for "a reactivation tool". Charging per result avoids that comparison.

## 4. How many old quotes come back (agenda 7.2)

| Metric | Figure | Conf. |
|---|---|---|
| Reply rate, SMS + email to dormant contacts | 2-8% | Low-Med |
| Reply rate, SMS only | 5-15% (avg ~8%) | Low |
| **Old-quote follow-ups specifically** | **5-8% reply, 2-4% booked** | Low |
| Replies that become bookings with fast response | 30-50% | Low |
| Vendor average booked rate | 4.4% (peak 8.9%) | Low (vendor) |

Sources: [LeadsNow](https://leadsnow.ai/how-to-run-a-database-reactivation-campaign/), [HL Growth Partner](https://hlgrowthpartner.com/post/gohighlevel-database-reactivation-campaign-2026), [AudienceIntent](https://www.audienceintent.ai/insights/10-ways-we-reactivate-leads-sitting-dormant-in-your-crm/). All vendors selling DBR, mostly US; discount heavily.

**What it means: the big strategic finding.**
A typical installer with ~1,500 old quotes × 2-4% booked ≈ **30-60
surveys, once**. At ~£150/survey that's **£4.5k-£9k per client, one-off**.
To reach £100k/month on one-off reactivation you'd need ~15 new clients
every month, forever. **One-off reactivation can't carry the business.**
It's the *door-opener*; the recurring product has to be something like
**following up every new quote automatically** (plus reviews/referrals),
billed monthly or per survey on an ongoing basis. This should shape the
offer before we write the pitch.

**Contrast with:** owner's material on offers/retention; our first pilot's
actual numbers (the only data that really counts).

## 5. Where installers' data lives (agenda 2.2)

UK window/door-specific CRMs exist and are established: **Business Pilot**,
**AdminBase** (Ab Initio; claims to be the standard for UK double glazing
firms), **EasyBase**, eWorks Manager, Deelo. Many small firms likely still
use spreadsheets or paper. Sources: [Business Pilot](https://businesspilot.co.uk/window-door-crm/), [Ab Initio](https://www.abinitiosoftware.co.uk/best-crm-for-window-installers/), [EasyBase](https://easybase.co.uk/).

**What it means.**
- Export from these tools is the realistic onboarding path; we should
  know each one's export format before the first client call.
- These vendors are **partnership targets** (agenda 5.2): they sit on every
  installer's quote data. A "reactivate your old quotes" add-on/referral
  deal with one of them could be a distribution channel.
- *Open question:* what share of our 1,918 leads use each? Scan their
  websites for "Business Pilot"/"AdminBase" customer portal links later.

## 6. Legal for client campaigns: the most important finding (agenda 11.3)

| Point | Conf. | Source |
|---|---|---|
| A **quote request counts as "negotiations for a sale"**: soft opt-in can apply to past quote recipients | High | [ICO](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guidance-on-direct-marketing-using-electronic-mail/how-do-we-comply-with-the-pecr-electronic-mail-marketing-rules/) |
| BUT the business **must have offered an opt-out when it collected the details**; if it didn't, soft opt-in is not available | High | ICO (same page) |
| No stated expiry on soft opt-in; applies to email and SMS | High | ICO (same page) |
| Genuine **service messages** (no promotional content) aren't direct marketing | High | [ICO](https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/direct-marketing-and-regulatory-communications/) |
| Live marketing **calls** to individuals are allowed unless the number is on **TPS** (~22 million numbers registered) | High | [Wikipedia/TPS](https://en.wikipedia.org/wiki/Telephone_Preference_Service), [Decision Marketing](https://www.decisionmarketing.co.uk/news/death-knell-for-cold-calling-as-tps-reaches-22-million) |
| **Post** isn't covered by PECR (UK GDPR legitimate interests applies) | Med | general PECR scope |
| UK SMS: register an alphanumeric sender ID (1-2 weeks); BT blocks unregistered brand IDs; alphanumeric IDs can't take "STOP" replies, so an opt-out link is needed; quiet hours ~9am-8pm; ~3.5-4.5p per SMS via Twilio | Med | [Twilio](https://twilio.com/guidelines/gb/sms), [Esendex](https://www.esendex.co.uk/blog/post/uk-sms-regulations-the-dos-and-donts-of-sms-marketing/), [Softomate](https://www.softomatesolutions.com/blog/gohighlevel-pricing-uk/) |

**What it means.**
- Every client list splits three ways at onboarding: (a) contacts where an
  opt-out was offered at collection → email/SMS allowed; (b) no opt-out
  offered → **not** email/SMS; use phone (TPS-screened), post, or a pure
  service message about their own quote; (c) opted out → nothing.
- Many small installers probably never offered an opt-out on their quote
  forms. **Onboarding must check their quote form/process**, not just ask.
  (Already a field in `truth/clients/_template/compliance.yaml`.)
- Letters are an underused, legal channel for old quotes, and homeowners
  open post. Worth testing alongside SMS.

## 7. Cold email for Velarqo's own outreach (agenda 4.1, 4.2, 4.5)

| Fact | Value | Conf. |
|---|---|---|
| Average B2B cold email reply rate | ~1.5-3.5% | Med |
| Positive reply rate, typical programs | 0.3-1.4% | Med |
| "Good" well-targeted campaign | 2-4% reply; 5-10% for local-services/small-business targets | Med |
| Safe sends per Google Workspace inbox | ~30/day; max ~100 | Med |
| Warm-up before sending | ≥3 weeks, ramp 5→50/day, keep ~20% warm-up running | Med |
| Bulk-sender rules (Google/Yahoo/Microsoft) | complaints <0.3%, bounces <2%; SPF+DKIM (+DMARC) | High |

Sources: [Instantly benchmarks](https://instantly.ai/blog/cold-email-reply-rate-benchmarks?lng=en), [lemlist](https://lemlist.com/blog/cold-email-response-rate), [Smartlead](https://www.smartlead.ai/blog/cold-email-reply-rate), [MailReach](https://www.mailreach.co/blog/cold-email-deliverability-sending-strategy), [LeadHaste warm-up](https://leadhaste.com/blog/email-warmup-best-practices), [Clay](https://www.clay.com/blog/b2b-cold-email-deliverability).

**What it means, as a funnel for wave 1 (792 leads, 3-email sequence):**
~2-5% positive → **16-40 interested owners** → maybe 10-25 calls →
**2-6 clients**. Enough to get the first case studies. Sending capacity:
3 inboxes × 30/day ≈ 90/day → wave 1 first touches in ~2 weeks, after
~3 weeks of warm-up. **So: set up domains and inboxes now; warm-up is
the longest lead time we have.**

## 8. Spain: autónomo vs SL (agenda 11.1)

| Fact | Conf. |
|---|---|
| Autónomo pays IRPF (progressive 19%-47%); SL pays Impuesto de Sociedades 25% (15% for new companies' first years) | High |
| Break-even usually quoted at **€40k-€60k net profit/year**; above it an SL tends to win | Med |

Sources: [Billin](https://www.billin.net/blog/mejor-autonomo-sociedad/), [Billeo](https://www.billeo.es/blog/autonomo-o-sl-a-partir-de-cuanto-ganas-te-conviene-una-empresa-con-numeros).

**What it means.** Start as autónomo (cheap, fast); plan the switch to an SL
around €4k-€5k/month profit, i.e. very early on the road to £100k/month.
Confirm with a gestor.

---

## The five things this changes

1. **The offer must include a recurring part.** One-off reactivation ≈
   £5k-£9k per client once. The recurring piece (follow-up of every new
   quote) is what gets to £100k/month. *Decision for the owner.*
2. **Price per booked survey, anchored on survey value (~£1,900 revenue to
   them), not lead cost.** Hypothesis: £100-£200 per booked survey.
3. **Client onboarding must sort each list by legal basis.** Email/SMS
   only where an opt-out was offered at collection; phone (TPS-screened)
   and letters for the rest.
4. **Start domain + inbox warm-up now.** It's the longest lead time.
5. **Window-CRM vendors (AdminBase, Business Pilot, EasyBase) are a
   channel**, not just an export problem.

## Open, for the owner's material and our own tests

- Real old-quote win-back rates in UK windows (our pilot).
- What installers actually close from old quotes.
- Whether installers offered an opt-out on their quote forms (check 20
  websites' quote forms: we can do this from our snapshots).
- Per-survey price acceptance (ask on first calls).
