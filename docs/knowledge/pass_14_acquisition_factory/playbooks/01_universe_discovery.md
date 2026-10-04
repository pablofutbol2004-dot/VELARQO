# 01 — Universe discovery

## Goal

Create a broad candidate-company universe with reproducible provenance. Discovery should maximize recall; qualification later creates precision.

## Recommended layers for UK windows & doors

1. **Companies House advanced search** — active legal entities, location, company type and SIC filters.
2. **FENSA / Certass directories** — strong trade-membership/certification signal for replacement window/door installers.
3. **Company websites** — actual homeowner-facing services, service area, proof, quote CTA.
4. **Search/local directories** — catch firms whose SIC or certification data is incomplete.
5. **Existing 1,918-company queue** — preserve as a source layer, not unquestioned ground truth.

## Important limitation

SIC codes are discovery hints, not a perfect installer classifier. Businesses can have stale, broad or multiple SIC codes. Never eliminate a strong operating installer solely because its SIC is noisy, and never qualify a company solely because its SIC looks right.

## Discovery record minimum

`source_name, source_record_id, source_url, discovered_name, discovered_domain, company_number_if_known, observed_at`

## Automation boundary

Prefer documented APIs and permitted exports. Before automating collection from a directory/site, check its terms, robots/rate limits and licensing. The factory supports manual/imported discovery when automated collection is not permitted.
