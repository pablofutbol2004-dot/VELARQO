# US contractor list sources (web research, 12 Oct 2026)

Sonnet research agent. Prices come from the vendors' pages unless marked as third-party. Confirm a price before paying for anything.

## Recommendation
Expected cost: **about $100-200 for ~3,000 qualified firms with emails, in about a week.**

1. **Apify Google Maps scraper** (https://apify.com/compass/crawler-google-places).
   - From $1.50 per 1,000 places. Details and contact enrichment add about $2 per 1,000 each, so about $5.50 per 1,000 all-in (extrapolated from the page's examples).
   - About 10,000 raw places should leave about 3,000 firms with 100+ reviews, for about $55 (the yield is a guess).
2. **Email verification** with NeverBounce: about $8 per 1,000 (third-party source; confirm at neverbounce.com/pricing). About $40 for 5,000 addresses.
3. **Free state licence files** to add owner names and cross-check:
   - **Washington:** data.wa.gov dataset `m8qx-ubtq`, 160k rows, updated daily. Licence PDDL (free for any use). Fields: name, address, phone, specialty codes, principal name.
   - **Oregon CCB:** active licences as CSV at data.oregon.gov `g77e-6bhs`.
   - **California CSLB:** free master list (https://www.cslb.ca.gov/OnlineServices/DataPortal/ContractorList). No emails; terms of use not found.
   - **Florida DBPR:** files exist, but the fields and terms are unconfirmed.
   - **Texas:** has no statewide roofing or remodeler licence.
4. **Google Places API (New):** a clean-licensing alternative.
   - The Enterprise tier is needed for website, phone and reviews: 1,000 free requests per month, then $35 per 1,000 Text Search requests and $20 per 1,000 Place Details requests.
   - It returns no emails.
   - Check Google's terms on storing the data.
5. **Outscraper:** a backup scraper. First 500 records free, then $3 per 1,000 (third-party source).

## Gaps
- No source gives headcount, so review count is the only proxy for firm size.
- Hunter's free tier (50 a month) and Apollo's free tier are too small to matter.
- Unconfirmed: official prices for Outscraper, MillionVerifier and LeadMagic; Florida's terms; Google's storage terms.
