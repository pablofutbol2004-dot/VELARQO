# SMS compliance

Support Portal (Phone System): https://help.gohighlevel.com/support/solutions/48000415161

SMS carries real regulatory risk (TCPA in the US, equivalent regimes
elsewhere) that email doesn't carry to the same degree. Cold SMS outreach
without prior consent is a materially different risk profile than cold
email — do not assume the cold-outreach pipeline's email logic can be
pointed at an SMS provider unchanged.

## Rules for any future SMS channel in Velarqo

- **Consent required before first send** — reactivation of an existing
  customer database is a better fit for SMS than net-new cold outreach,
  since there's usually an existing relationship/consent basis; cold SMS
  to purchased/scraped lists is the highest-risk pattern and should not be
  built without explicit legal sign-off from the client.
- **Opt-out handling is mandatory and immediate.** `STOP`/`UNSUBSCRIBE`
  keywords must suppress that contact across all future sends, not just
  the current campaign. This maps directly onto
  `database_reactivation/segmentation/suppression.py`'s existing
  `unsubscribed` reason — an SMS opt-out should write to the same
  suppression state, not a separate SMS-only list.
- **A2P registration**: US SMS at any volume typically requires carrier
  A2P 10DLC registration per sending number/campaign type. This is a GHL/
  Twilio-level account setup step per client, not something Velarqo's code
  can route around.
- **Quiet hours**: respect local time-of-day sending windows per contact's
  region, not per Velarqo's own timezone.

Given this, SMS is a Tier 2/3 concern per `VELARQO_PRIORITY.md` — don't
build it ahead of getting email outreach and reactivation solid, and treat
it as needing its own compliance review when it does get built, not a
copy-paste of the email flow.
