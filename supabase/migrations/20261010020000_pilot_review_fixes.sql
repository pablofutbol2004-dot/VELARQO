-- Fixes from the delivery code review (2026-10-10).
-- person_key: one person can have several quotes (rows); group them so a
--   person is never split across holdout/treatment or texted twice.
-- claimed_at: claim order, for "first N homeowners free" (offer B).
-- ghl_calendar_id: only appointments on the pilot's survey calendar count.
-- max_billable / max_billable_per_week / free_homeowners: agreement terms.

alter table public.pilot_homeowners add column person_key text;
alter table public.pilot_homeowners add column claimed_at timestamptz;
create index pilot_homeowners_person on public.pilot_homeowners (pilot_id, person_key);

alter table public.pilots add column ghl_calendar_id text;
alter table public.pilots add column max_billable integer check (max_billable is null or max_billable >= 0);
alter table public.pilots add column max_billable_per_week integer check (max_billable_per_week is null or max_billable_per_week >= 0);
alter table public.pilots add column free_homeowners integer not null default 0 check (free_homeowners >= 0);
