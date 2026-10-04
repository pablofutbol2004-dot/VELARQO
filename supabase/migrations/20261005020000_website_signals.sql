-- Signals read from the latest stored website text (no extra fetching).
-- Each is a fact the installer states about themselves, usable as a
-- segment or, carefully, in copy.

create view public.website_signals with (security_invoker = true) as
with latest as (
  select distinct on (company_id)
    company_id, lower(coalesce(title, '') || ' ' || coalesce(text, '')) as page, fetched_at
  from public.website_snapshots
  order by company_id, fetched_at desc
)
select
  company_id,
  page ~ 'checkatrade' as on_checkatrade,
  page ~ 'trustpilot' as on_trustpilot,
  page ~ '(which\?|which trusted trader)' as which_trusted_trader,
  page ~ '(mybuilder|rated ?people|trustatrader|bark\.com)' as on_lead_marketplace,
  page ~ '(google reviews|5 ?star|★)' as mentions_reviews,
  page ~ '(finance available|interest.?free|pay monthly|buy now pay later|0% finance|spread the cost)' as offers_finance,
  page ~ '(showroom|visit our show)' as has_showroom,
  page ~ '(instant quote|online quote|quote calculator|price calculator|get a price online|design your (own )?(window|door))' as online_quoting,
  page ~ '(family.?run|family business|family.?owned)' as family_run,
  page ~ '(no.?pressure|no (hard|pushy) ?sell|no pushy|no sales ?(men|man|people|person|calls))' as no_pressure_sales,
  (regexp_match(page, '(?:established|est\.?|since|founded)\s+(?:in\s+)?(19[5-9]\d|20[0-2]\d)'))[1]::int as established_year,
  (regexp_match(page, '(\d{1,2})\+?\s+years?.{0,15}(?:experience|in business|trading)'))[1]::int as years_claimed,
  fetched_at
from latest;

revoke all on public.website_signals from anon, authenticated;
grant select on public.website_signals to velarqo_loader;
