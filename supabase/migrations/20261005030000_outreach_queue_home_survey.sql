-- Adds home_survey: the installer's own site says they visit to survey or
-- measure before quoting. Segment for the 'trip out to measure' copy test.

create or replace view keeps working.

create or replace view public.outreach_queue with (security_invoker = true) as
with latest as (
  select distinct on (company_id)
    company_id, lower(coalesce(title, '') || ' ' || coalesce(text, '')) as page
  from public.website_snapshots
  order by company_id, fetched_at desc
),
base as (
  select c.*,
    coalesce(l.page, lower(coalesce(c.website_title, ''))) as page,
    lower(split_part(c.email, '@', 2)) as email_domain,
    date_part('year', age(current_date, c.incorporation_date))::int as years_trading
  from public.companies c
  left join latest l on l.company_id = c.id
  where c.vertical = 'windows' and c.tier in ('A', 'B') and c.email is not null
),
signals as (
  select b.*,
    b.page ~ '(for sale|buy this domain|brandbucket|hugedomains|sedo\.com|dan\.com|domain parking)' as parked,
    b.page ~ '(double.?glaz|glazing|glazier|upvc|pvcu|sash window|casement|replacement window|new windows|windows and doors|windows & doors|doors and windows|bi.?fold|composite door|front door|french door|patio door|conservator|orangery|secondary glazing|misted|sealed unit)' as trade,
    b.page ~ '(manufactur|trade only|trade counter|trade supplier|wholesale|fabricat|systems house|distributor)'
      and not b.page ~ '(homeowner|your home|free quote|installation)' as supplier_only,
    b.page ~ '(homeowner|your home|free quote|no.obligation|home improvement|fensa|certass|double glazing|replacement windows)' as residential,
    b.page ~ '(fire door|automatic door|industrial door|roller shutter|loading bay|curtain wall|shopfront)' as commercial,
    (b.email_domain ~ '\.uk$'
      or b.page || ' ' || b.email_domain ~ '(united kingdom|\muk\M|england|scotland|wales|northern ireland|london|\+44|\m0[1-3]\d{2,4} ?\d{3}|\m07\d{3} ?\d{3} ?\d{3}|\m[a-z]{1,2}\d[a-z\d]? ?\d[a-z]{2}\M|yorkshire|lancashire|middlesex|essex|kent|surrey|sussex|hampshire|devon|cornwall|dorset|somerset|norfolk|suffolk|cheshire|cumbria|durham|northumberland|shropshire|staffordshire|warwickshire|leicestershire|derbyshire|nottinghamshire|lincolnshire|berkshire|oxfordshire|buckinghamshire|hertfordshire|bedfordshire|cambridgeshire|wiltshire|gloucestershire|worcestershire|herefordshire|merseyside|midlands)') as uk,
    (b.extra ? 'accreditations' or b.page ~ '(fensa|certass)') as accredited,
    split_part(b.email, '@', 1) ~* '^(info|sales|enq|office|contact|hello|admin|e?mail|accounts|support|service|reception|quotes?|team|web)|^(cs|group)$' as generic_inbox,
    b.page ~ '(no.?pressure|no (hard|pushy) ?sell|no pushy|no sales ?(men|man|people|person|calls)|do not employ sales|don.?t employ sales)' as no_pressure_sales,
    b.page ~ '(free (home )?survey|home survey|home visit|survey (at|of) your (home|property)|(come|call) (round|out|to you) (to|and) measure|measure ?up|visit (you|your home|your property) to|in.?home (consultation|survey|appointment|visit)|free,? no.?obligation (home )?(visit|consultation|survey))' as home_survey
  from base b
),
scored as (
  select s.*,
    least(greatest(coalesce(s.years_trading, 0), 0), 10) * 4 as p_years,
    case
      when s.accounts_category in ('TOTAL EXEMPTION FULL', 'UNAUDITED ABRIDGED', 'SMALL', 'TOTAL EXEMPTION SMALL') then 25
      when s.accounts_category = 'MICRO ENTITY' then 18
      when s.accounts_category in ('MEDIUM', 'FULL', 'GROUP', 'AUDIT EXEMPTION SUBSIDIARY') then 12
      when s.accounts_category = 'NO ACCOUNTS FILED' then 3
      else 8
    end as p_size,
    case when s.accredited then 15 else 0 end as p_accredited,
    case when s.residential then 10 else 0 end as p_residential,
    case when s.generic_inbox then 0 else 10 end as p_named_inbox
  from signals s
)
select
  id, display_name, legal_name, company_number, email, phone, website, city, postcode,
  tier, years_trading, accounts_category, company_category, accredited, residential, generic_inbox,
  (p_years + p_size + p_accredited + p_residential + p_named_inbox) as priority,
  jsonb_build_object(
    'years_trading', p_years, 'size', p_size, 'accredited', p_accredited,
    'residential', p_residential, 'named_inbox', p_named_inbox
  ) as priority_breakdown,
  no_pressure_sales,
  home_survey
from scored q
where not parked
  and trade
  and not supplier_only
  and not (commercial and not residential)
  and uk
  and coalesce(company_category, 'Limited Partnership') <> 'Limited Partnership'
  and not exists (
    select 1 from public.suppressions x
    where lower(x.email) = lower(q.email) or lower(x.domain) = q.email_domain
  );

revoke all on public.outreach_queue from anon, authenticated;
grant select on public.outreach_queue to velarqo_loader;
