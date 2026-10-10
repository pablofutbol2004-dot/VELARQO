-- Which GoHighLevel sub-account (location) belongs to which pilot, so
-- incoming webhooks are routed to the right client and nothing else.

alter table public.pilots add column ghl_location_id text unique;
create index pilot_homeowners_ghl_contact on public.pilot_homeowners (ghl_contact_id) where ghl_contact_id is not null;
