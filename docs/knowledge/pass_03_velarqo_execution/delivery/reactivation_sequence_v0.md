# Homeowner reactivation sequence v0

**Use only for contacts that pass the compliance gate.** Client must approve the exact wording and any offer.

The goal is to restart a legitimate old conversation, not manufacture urgency.

## Default SMS — neutral, contextual
### Touch 1 — Day 0
> Hi {{first_name}}, it’s {{sender_name}} from {{company}}. You asked us about {{job_type}} a while back and I wanted to check — is it still something you’re considering? Reply STOP if you’d rather not hear from us.

Why: recognisable context + easy yes/no response. No discount needed.

### Touch 2 — Day 3–4, only if no reply
> Hi {{first_name}}, just following up on the {{job_type}} quote. If the project is still on the list, we can take another look / update the quote. Want me to arrange that? Reply STOP to opt out.

Only say “update the quote” if client can genuinely do so.

### Touch 3 — Day 8–10, only if no reply
> Last message from me, {{first_name}}. If the {{job_type}} project is still relevant, reply YES and we’ll get it picked back up. If not, no problem. Reply STOP to opt out.

If we say “last message,” it must actually be the last sequence touch.

## Email equivalent
Subject: `your {{company}} quote`

Hi {{first_name}},

You asked us about {{job_type}} a while back and I wanted to check whether it’s still something you’re considering.

If it is, we can pick it back up and arrange the next step / update the quote.

Still relevant?

{{sender_name}}
{{company}}

[clear opt-out mechanism]

## Segmentation variants to test later
Do not deploy until the basic sequence has data.

### Lost on timing / postponed
Reference timing, not a generic promotion.
> You mentioned the timing wasn't right when we last spoke — has that changed at all?

### Quote expired / old price
Do not imply old price remains valid.
> The old quote may no longer be current, but if the project is still live we can re-check it for you.

### No-show / missed survey
> We never managed to get the survey done. Is the project still something you want to revisit?

### Bought elsewhere
Do **not** try to book the original job. Close/suppress from sales reactivation; any referral/review/customer campaign is a separate purpose and eligibility decision.

## Message principles
- one question per message;
- plain language;
- no fake scarcity;
- no fabricated discount;
- no pretending a human personally remembered the contact if the campaign is automated;
- client brand/sender should be clear;
- stop immediately on opt-out;
- shorten before adding cleverness.
