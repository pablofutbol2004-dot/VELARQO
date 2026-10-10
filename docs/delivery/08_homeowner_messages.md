# Homeowner messages: sequence, replies and escalation

Sent in the installer's name from their GoHighLevel sub-account (UK number,
their email). The installer approves every word on `09` before anything
goes out. Any wording change = a new approval.

**Placeholders** (filled per homeowner from the export):
[first name] · [sender] = the name on the intake form (a real person at the
installer, or "the team") · [Installer] = their trading name ·
[product] = what was quoted, as it reads after "a quote for" ("new windows",
"a new front door", "a new roof") · [when] = roughly when ("last March", "in the spring").
If [product] or [when] is missing for a homeowner, use the fallback
version of that line, never a guess.

**Rules for every message**
- Texts: plain GSM characters only (straight apostrophes, no emojis, no
  curly quotes), or each text costs more and splits early. Under 300
  characters when filled.
- Every text names [Installer] and ends "Reply STOP to opt out".
- The sequence stops for good the moment the homeowner replies, opts out,
  or books.
- Send 9am-7pm, Monday to Saturday. No Sundays or bank holidays.
- No discounts, deadlines or "only this week" unless the installer has
  approved a real offer.

## The sequence (about 2 weeks)

**Text 1, day 0 — version A** (random half)
> Hi [first name], it's [sender] at [Installer]. You asked us to quote for [product] [when]. Did you ever get that sorted? If not, we're happy to take another look. Reply STOP to opt out

**Text 1, day 0 — version B** (other half)
> Hi [first name], [sender] here from [Installer]. We quoted you for [product] [when] but it didn't go ahead. Is it still something you're thinking about? Reply STOP to opt out

**Text 2, day 3** (no reply yet)
> Hi [first name], [sender] at [Installer] again. If the [product] job is still on your list, we can come out, re-measure and give you an up-to-date price, no obligation. Want me to suggest a couple of times? Reply STOP to opt out

**Email, day 7** (no reply yet)

Subject: your [product] quote

> Hi [first name],
>
> You asked [Installer] for a quote for [product] [when], and I wanted to
> check whether it's still something you're considering.
>
> Prices may have changed since, so the old quote might not be current.
> If you'd like, we can come out, take another look and give you an
> up-to-date price. No obligation.
>
> Just reply to this email and I'll suggest a couple of times.
>
> [sender]
> [Installer], [phone], [website]
>
> You're getting this because you asked [Installer] for a quote. If you'd
> rather not hear from us again, reply "stop" or [unsubscribe link].

**Text 3, day 12** (no reply yet; really the last one)
> Last message from me about this, [first name]. If you'd still like [Installer] to quote for [product], reply YES and I'll send a couple of survey times. If not, no problem at all. Reply STOP to opt out

**Fallbacks:** no [when] → "a while back". No [product] → don't send;
ask the installer to fill it in for those quotes.

## Replies (answered by Pablo in [Installer]'s name, within 1 working hour)

**Interested → offer 2 slots**
> Great, thanks [first name]. Is it still [product] at [postcode]? We could come out on [slot 1] or [slot 2]. Which suits you best? It takes about [length] and there's no obligation.

**Booking confirmed**
> Booked: [slot] at [first line of address]. [surveyor name] from [Installer] will come out. If you need to change it, just reply here.

**Reminder, day before** (if the booking is more than a day away)
> Hi [first name], just a reminder that [surveyor name] from [Installer] is coming tomorrow, [day, time], to measure up for [product]. Reply here if you need to change it.

**Reminder, morning of**
> Morning [first name], [surveyor name] from [Installer] will see you today at [time]. Reply here if anything's changed.

**"How much is it now?"**
> Prices have moved since the old quote, so I don't want to give you a wrong figure by text. [surveyor name] can re-check it and give you an up-to-date price on the spot, no obligation. Would [slot 1] or [slot 2] work?

If they push for a number or argue about the old price → escalate.

**"Already done it" / "went elsewhere"**
> Thanks for letting me know, [first name], hope it all went well. I'll close this off and we won't message you about it again.

Mark closed (lost, "done elsewhere"). Never try to win it back.

**"Not now, maybe later"**
> No problem at all. Would you like us to get back in touch at a better time, say [month], or shall I leave it there?

Only if they name a time: record it and pass it to [Installer]. We don't
schedule more messages ourselves in the pilot. If they say leave it: close
and don't contact again.

**"Who is this?" / "How did you get my number?"**
> It's the team at [Installer] in [town]. You asked [Installer] for a quote for [product] [when], and we're just checking if you're still interested. We're a small service that follows up [Installer]'s old quotes for them. If you'd rather not hear from us again, reply STOP and we won't.

(Answer truthfully: whoever types the reply is not [sender]. Say "the team at
[Installer]" and mention the follow-up service, never pretend to be a named
person at the installer.)

If they ask whether a company is sending it for [Installer]:
> Yes, [Installer] uses a small follow-up service, Velarqo, to send these messages for them. Your details came from your own quote request to [Installer]; they haven't been sold or passed on for anyone else to market to you.

Log every "how did you get my number" as a complaint signal (it counts
towards the pause limit in `04`, section 8) and tell the installer.

**STOP / "remove me" / "don't contact me"**
No sales reply. GoHighLevel should mark the contact as do-not-disturb
automatically on STOP [to confirm in the test send, map step 8.6]. Any
other wording ("remove me", "leave me alone"): set it by hand at once,
and tell the installer to add them to their own list. If anything is sent,
only a one-line confirmation:
> Done, you won't hear from us again.

## Escalation: a person decides, never a template

Stop the conversation, don't reply with a template, and pass it to Pablo
straight away; Pablo tells the installer's named contact the same working
day:
- **Complaints** or anger, swearing, threats.
- **Mentions of the ICO, a regulator, a solicitor, or "GDPR"**, or a request
  to see or delete their data (goes to the installer within 2 working days,
  per `05`).
- **Pricing disputes**: arguing about the old quote, asking for a discount,
  finance terms, guarantees.
- **Vulnerable people or sensitive news**: bereavement, illness, money
  trouble, confusion, very elderly, "my husband died". Close kindly,
  suppress, tell the installer.
- **Wrong person, moved house, deceased.** Suppress; count as wrong-person.
- **Anything about a previous job, a fault or a dispute** with the installer.
- **Technical questions** we can't answer from the approved wording.
- **Any reply we don't understand.**

In the pilot every reply is read and answered by Pablo. Nothing replies
automatically except the scheduled sequence, booking confirmations and
reminders.
