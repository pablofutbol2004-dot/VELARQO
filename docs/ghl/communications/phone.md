# Phone system

Support Portal: https://help.gohighlevel.com/support/solutions/48000415161

GHL's LC Phone System (Twilio-backed) covers calls, voicemail drops, and
call tracking/recording. Tier 2 per `VELARQO_PRIORITY.md` — relevant once a
client wants call tracking/attribution on top of the appointment/sale
pipeline, but not required for the core cold-outreach or
database-reactivation loops, which are email-first today.

If/when this gets built: call outcome events (answered, voicemail, missed)
are a natural additional input to `lib/tracking/experiments.py` — a call
attempt is another touch on the same `experiment_result` row, not a
separate tracking table.
