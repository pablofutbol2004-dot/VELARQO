# Message approval sheet

For [Installer] · Pilot [pilot_id] · Version [v1]

These are the exact messages that will be sent to your old quotes, in your
name. Please read each one, tick it if you're happy, or write the change you
want next to it. **Nothing is sent until every message below is ticked and
this sheet is signed.**

Words in [square brackets] are filled in for each homeowner from your
export: [first name], [product] (what you quoted, e.g. "new windows"),
[when] (roughly when, e.g. "last March"), survey times from your calendar.
Signed with: **[sender]** · Your trading name: **[Installer]**

Before you tick, check:
- every offer in here is one you'll honour (coming out to re-measure, an
  up-to-date price on the day, no obligation);
- the person or name signing the messages is happy to be used.

## Sequence (stops as soon as the homeowner replies)

☐ **Text 1A, day 0** (half the list)
Hi [first name], it's [sender] at [Installer]. You asked us to quote for [product] [when]. Did you ever get that sorted? If not, we're happy to take another look. Reply STOP to opt out

☐ **Text 1B, day 0** (the other half)
Hi [first name], [sender] here from [Installer]. We quoted you for [product] [when] but it didn't go ahead. Is it still something you're thinking about? Reply STOP to opt out

☐ **Text 2, day 3**
Hi [first name], [sender] at [Installer] again. If the [product] job is still on your list, we can come out, re-measure and give you an up-to-date price, no obligation. Want me to suggest a couple of times? Reply STOP to opt out

☐ **Email, day 7** — Subject: your [product] quote
Hi [first name],
You asked [Installer] for a quote for [product] [when], and I wanted to check whether it's still something you're considering.
Prices may have changed since, so the old quote might not be current. If you'd like, we can come out, take another look and give you an up-to-date price. No obligation.
Just reply to this email and I'll suggest a couple of times.
[sender]
[Installer], [phone], [website]
You're getting this because you asked [Installer] for a quote. If you'd rather not hear from us again, reply "stop" or [unsubscribe link].

☐ **Text 3, day 12** (the last one)
Last message from me about this, [first name]. If you'd still like [Installer] to quote for [product], reply YES and I'll send a couple of survey times. If not, no problem at all. Reply STOP to opt out

## Replies and bookings

☐ **Interested**
Great, thanks [first name]. Is it still [product] at [postcode]? We could come out on [slot 1] or [slot 2]. Which suits you best? It takes about [length] and there's no obligation.

☐ **Booking confirmed**
Booked: [slot] at [first line of address]. [surveyor name] from [Installer] will come out. If you need to change it, just reply here.

☐ **Reminder, day before**
Hi [first name], just a reminder that [surveyor name] from [Installer] is coming tomorrow, [day, time], to measure up for [product]. Reply here if you need to change it.

☐ **Reminder, morning of**
Morning [first name], [surveyor name] from [Installer] will see you today at [time]. Reply here if anything's changed.

☐ **"How much is it now?"**
Prices have moved since the old quote, so I don't want to give you a wrong figure by text. [surveyor name] can re-check it and give you an up-to-date price on the spot, no obligation. Would [slot 1] or [slot 2] work?

☐ **"Already done it"**
Thanks for letting me know, [first name], hope it all went well. I'll close this off and we won't message you about it again.

☐ **"Not now, maybe later"**
No problem at all. Would you like us to get back in touch at a better time, say [month], or shall I leave it there?

☐ **"Who is this? How did you get my number?"**
It's [sender] at [Installer] in [town]. You asked us for a quote for [product] [when], and we're just checking if you're still interested. If you'd rather we didn't contact you again, reply STOP and we won't.

☐ **"Is a company sending this for you?"**
Yes, [Installer] uses a small follow-up service, Velarqo, to send these messages for them. Your details came from your own quote request to [Installer]; they haven't been sold or passed on for anyone else to market to you.

☐ **Opt-out confirmation** (only if one is sent)
Done, you won't hear from us again.

Anything else (complaints, price arguments, upset or vulnerable people) is
not answered from a template. It comes to you, as agreed in the pilot terms.

## Sign-off

I approve the messages above, exactly as written. I understand that **any
change to any message, however small, needs a new approval** before it is
used. Velarqo keeps a copy of the approved wording with a digital
fingerprint of it, so we can both check later that nothing was changed.

Name: ______________ Role: ______________

Signature: ______________ Date: ______

---

Notes for Pablo (delete before sending)
- Copy the ticked message texts, exactly as approved, into
  `clients/<slug>/approved_messages_v<n>.txt`, then:
  `python -m delivery.pilot approve <pilot_id> messages --actor "<their name>" --messages-file clients/<slug>/approved_messages_v<n>.txt --note "signed sheet v<n>, <date>"`.
  The CLI stores the text and its SHA-256 hash. Keep the signed PDF next to it.
- Paste the GHL workflow texts **from that file**, not from this doc, so
  what's sent is what was approved.
- If they change a message, update `08_homeowner_messages.md` only if the
  change should apply to future clients too.
