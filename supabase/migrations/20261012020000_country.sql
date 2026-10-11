-- Second market groundwork (Ireland, CRO open data): every company row says
-- which country's register and law it falls under. Existing rows are all UK
-- (default). The send list (outreach_queue) stays UK-only until the Irish
-- footer and sender details exist (docs/IRELAND.md).
--
-- The view is edited in place from its live definition instead of being
-- restated: other sessions rewrite outreach_queue too (kitchens, review
-- fixes), and a restated body here would silently undo whichever of them
-- applied first. Whoever rewrites the view next must keep the filter
-- `c.country = 'UK'` in the base CTE (tests/integration/test_country_guard.py
-- fails when the newest rewrite lacks it).

-- Other sessions read the view for minutes at a time; give up rather than
-- queue behind them and block everyone (apply_migration is one transaction,
-- so nothing half-applies) and retry later.
set lock_timeout = '20s';

alter table public.companies
  add column country text not null default 'UK'
  check (country ~ '^[A-Z]{2}$');

-- Company numbers are only unique within one register.
alter table public.companies drop constraint companies_vertical_company_number_key;
alter table public.companies add constraint companies_vertical_country_company_number_key
  unique (vertical, country, company_number);

create index companies_country_vertical_tier_idx on public.companies (country, vertical, tier);

do $$
declare
  def text;
  new_def text;
begin
  def := pg_get_viewdef('public.outreach_queue'::regclass, true);
  if def like '%c.country = ''UK''%' then
    return;
  end if;
  new_def := regexp_replace(def, 'WHERE \(c\.vertical = ANY', 'WHERE c.country = ''UK''::text AND (c.vertical = ANY');
  if new_def = def then
    raise exception 'outreach_queue: base filter "WHERE (c.vertical = ANY" not found; add c.country = ''UK'' by hand';
  end if;
  drop view public.outreach_queue;
  execute 'create view public.outreach_queue with (security_invoker = true) as ' || new_def;
  revoke all on public.outreach_queue from anon, authenticated;
  grant select on public.outreach_queue to velarqo_loader;
end
$$;
