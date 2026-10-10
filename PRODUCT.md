# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: plain static HTML/CSS in `website/`, no build step, deployed to Cloudflare Pages on velarqo.com. Chosen because the site is a few pages, the founder is not a developer, and it must be free and fast.

## Users

Owners and managers of UK window and door installation firms and domestic roofing firms (roughly 10–500 staff). They arrive from a short cold email from Velarqo, usually on a phone, between jobs or in the evening. Their job on the site: decide in under a minute whether this is a real person with a credible offer, or spam. Trades owners are practical, sceptical of marketing, and allergic to tech-startup talk.

## Product Purpose

Velarqo runs follow-up campaigns on a firm's old, unconverted quotes (homeowners who were quoted and went quiet) and turns a share of them into booked appointments. The site exists to make the cold email credible and get the owner to reply or get in touch. Success = a reply or an email to hello@velarqo.com.

## Positioning

Not lead generation from strangers: it works the firm's own old quotes, leads they already paid to create. Performance-based: "You only pay for surveys that get booked." (Never "nothing to pay unless it works" or "pay only if it works": they pay per booked survey even if no sale follows.) A one-person operation run by the founder personally, not an agency with account managers.

## Operating Context

- Contact: hello@velarqo.com (forwards to the founder's Gmail via Cloudflare Email Routing).
- The founder is based in Spain and will operate as an autónomo (not yet registered); clients are in the UK. Spanish LSSI requires an "aviso legal" with the operator's identity; UK and EU GDPR both apply.
- Client data arrives as spreadsheets or CRM/job-system exports; Velarqo acts as data processor for it.

## Capabilities and Constraints

- Billing unit: decided 2026-10-04, a fee per booked survey. The price itself is tested on calls (`docs/PRICING.md`) and recorded only in the signed agreement and invoices. **No price in marketing copy or emails** (website, cold emails, replies in writing). This rule covers marketing and emails only, not contracts or invoices, which must state the price.
- Say: "You only pay for surveys that get booked" and "terms agreed before anything starts". Never say "nothing to pay unless it works".
- Verticals: window and door installers, and roofing (`cold_roofing_v1`). The offer is the same.
- No booking tool yet; the CTA is email.
- Legal identity: founder's full name and address to be supplied and put on the site before the first cold email; NIF added once registered as autónomo.

## Brand Commitments

- Name: Velarqo. Domain: velarqo.com.
- Voice: plain, direct, British English, short sentences, no hype, no jargon ("leverage", "AI-powered", "growth"). Talks like a tradesperson would.
- Logo: lowercase "velarqo" wordmark in black with a coral-red tail on the q, plus a "VQ" monogram. Source: `brand/logo-source.webp`; web crops in `website/logo.png` and `website/icon.png`. A vector (SVG) version is still wanted.

## Evidence on Hand

- None yet. Pre-revenue, no clients, no case studies, no testimonials, no results figures. Never fabricate any of these, and never imply a track record.
- Founder photo: promised, not yet supplied. Design must have a place for it and work without it until then.

## Product Principles

1. Credibility over cleverness: every element should make a sceptical trades owner more likely to believe a real person is behind this.
2. Honesty is the pitch: say plainly what is and isn't known yet (new service, you only pay for surveys that get booked).
3. Their world, not ours: speak in quotes, surveys, fitters and diaries, not funnels and pipelines.
4. Fast on a phone: the first screen must land on a small screen with a weak signal.

## Accessibility & Inclusion

WCAG 2.2 AA. Many readers are older and read on phones outdoors: generous type size, strong contrast.
