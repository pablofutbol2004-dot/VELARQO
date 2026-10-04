-- Applied to the live DB on 2026-09-30 outside the repo; saved here 2026-10-01
-- so the repo matches the database.
alter table public.companies
  add column if not exists phone_source text,
  add column if not exists phones_found text[] not null default '{}';

alter table public.website_snapshots
  add column if not exists phones_found text[] not null default '{}';
