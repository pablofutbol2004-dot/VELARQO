# Cold-email legality by country + DBR niche atlas (web research, 2026-10-10)

Source: Claude web-research agent, ~28 searches/fetches. Tags: P primary (regulator/statute), S secondary, V vendor, G guess. ACMA, NZ legislation and CRTC blocked fetches, so AU/NZ penalties are not primary.

## Cold email to companies, by country

| Country | Verdict | Conditions | Max fine | Source |
|---|---|---|---|---|
| UK | Yes | Corporate subscribers (Ltd/LLP); identity + opt-out; sole traders = individuals | up to £17.5m/4% after DUAA 2025 (S, verify commencement) | ICO (P) |
| Ireland | Yes | Reg 13(4): non-natural-person subscribers until they object; sole traders only if address is business-use and message relates to that business; contact address, no disguised sender; burden of proof on sender | €250k/offence on indictment; €5k/message summary (S) | S.I. 336/2011 (P) |
| USA | Yes | CAN-SPAM: no B2B exception needed; accurate headers, postal address, opt-out honoured in 10 days | up to $53,088/email | FTC (P) |
| Australia | Conditional | Inferred consent only if address conspicuously published, no "no marketing" note, relevant to role; ACMA calls it narrow | penalty units/day; CBA fined A$7.5m 2024 | ACMA, Spam Act (S) |
| New Zealand | Conditional | Deemed consent, same three limbs; sender must prove consent | ~NZ$200k individual / 500k others (G) | DIA, Act (S) |
| Canada | Conditional | CASL s10(9)(b) implied consent via conspicuous publication, relevant to role; unsubscribe + ID; CRTC says narrow | C$10m/violation companies | CASL (P) |
| France | Conditional | Legitimate interest if subject relates to profession; inform + right to object; French language | GDPR-level | CNIL (P) |
| Germany | No | UWG §7(2) no.3: prior express consent for email ads | warning letters/injunctions | UWG (P) |
| Netherlands | No (in practice) | Telecommunicatiewet 11.7: prior consent; exception only for addresses published to receive commercial mail | ~€900k/breach (S) | wetten.overheid.nl (P) |
| Italy | No | Privacy Code art 130: consent; no B2B carve-out | not confirmed | Agenda Digitale (S) |
| Spain | No | LSSI art 21 | €30k minor / €150k serious | BOE (P) |

Notes: homeowner messages follow the destination country's consumer rules (e.g. CASL: existing relationship 2 years after purchase, 6 months after inquiry). Ireland is the closest copy of the UK (English, PECR-like split).

Registers: Ireland CRO free API (basic data; industry filter unconfirmed); 600+ SEAI heat-pump contractors. Australia ASIC free weekly dataset (no industry code), ABN Lookup free; ~8,255 accredited solar installers (S, old). NZ NZBN API free; small market. France INSEE Sirene free API by NAF code (4332A ~60,700; 4391B roofing 15-23k, unreliable). USA/Canada: no register data found.

## Niche atlas (UK)

Counts found: Glazing 43342 2,818 (IBISWorld, undercounts fitters under 43320/43999); MCS 5,636 active contractors Q4 2025, 4,066 solar-certified early 2025; Gas Safe ~80,014 businesses (mostly sole traders, G).

Our own count from the Companies House bulk file (active Ltd/LLP, non-dormant, 2026-09-01; SIC or name match): windows/doors/glazing 9,981; roofing 18,145; kitchens 8,827; bathrooms 2,967; solar/battery 4,513; heating/heat pump 48,408 (SIC 43220, mostly plumbers); driveways/paving 2,853; landscaping 23,040; garage doors 304; stairlifts/mobility 1,158; flooring 13,437; builders/extensions 91,673; electrical/EV 53,068; blinds/shutters 2,611; damp/insulation 3,848; dental 20,146; aesthetics 8,366; gyms 17,923; car dealers 44,433; estate/letting agents 158,296.

| # | Niche | Job value | Why |
|---|---|---|---|
| 1 | Windows, doors, conservatories | £6-14k; conservatories £10-17k+ | Written quotes going quiet is the core pain |
| 2 | Kitchens | £7-25k | Long consideration, written quotes |
| 3 | Bathrooms | ~£7k | Same pattern, lower value, many sole traders (G) |
| 4 | Solar + battery | £5.5-14k | Strong quote pain; summer-skewed, policy-dependent (G) |
| 5 | Heat pumps | £8-11k | Grant-led, slow decisions. Boilers are emergency buys: no |
| 6 | Lofts/extensions | £40k+ (G) | Huge value, long cycle, mostly sole traders (G) |
| 7 | Dental implants/cosmetic | £2-15k (G) | "Unaccepted treatment plan" = quiet quote; clinical-data friction |
| 8 | Driveways/paving/garden rooms | £5-15k (G) | Quotes go quiet; mostly sole traders (G) |

"Quote went quiet" niches: windows/conservatories, kitchens, bathrooms, solar, heat pumps, lofts, driveways/landscaping, roofing, garage doors, stairlifts, blinds, damp proofing, dental implants, estate agents (valuations not instructed).
"Lapsed customer" niches: gyms, aesthetic clinics, hearing aids, private physio, car dealer servicing, letting agents, boiler servicing.

DBR evidence is thin and vendor-sourced (V): Xpand Digital floor-sanding 96 quotes → 5 jobs, roofer 5.2% close on 3-year-old leads (unverifiable); mortgage broker 319 → 75 appointments; aesthetic clinic 5,692 lapsed → 722 booked (Aesthetix); estate agents ~6% vs 1.2% (Klosed). A York dental practice found SMS/postcards to lapsed patients drew little (Dentistry.co.uk 2014). No independent case studies for kitchens, solar or windows.
