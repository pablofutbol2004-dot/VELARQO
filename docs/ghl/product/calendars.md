# Calendars & appointments

Support Portal: https://help.gohighlevel.com/support/solutions/48000449585

Booking, availability, round robin, rooms/equipment, services.

## Relevant webhooks

`AppointmentCreate`, `AppointmentUpdate`, `AppointmentDelete` — see
`api/WEBHOOKS.md`.

## Mapping onto Velarqo's schema

`AppointmentCreate` for a contact whose GHL id matches a
`experiment_result.lead_id` -> call
`lib/tracking/experiments.py::record_appointment(experiment_id)`.

For the database-reactivation flow specifically: a client's existing
booking calendar/availability config in GHL should be treated as fixed —
Velarqo generates the *lead* and the *campaign angle*, GHL handles the
actual scheduling UI/logic (matches the `VELARQO_PRIORITY.md` split:
"appointment booking" stays inside GHL).
