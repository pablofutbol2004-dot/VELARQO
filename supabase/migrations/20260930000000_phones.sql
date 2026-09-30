-- UK phone numbers found on a company's own website. Phone may be the
-- lawful first-contact channel while cold email is blocked (see
-- truth/velarqo/compliance.yaml), so it gets the same provenance as email.
alter table public.companies
  add column if not exists phone_source text,
  add column if not exists phones_found text[] not null default '{}';

alter table public.website_snapshots
  add column if not exists phones_found text[] not null default '{}';
