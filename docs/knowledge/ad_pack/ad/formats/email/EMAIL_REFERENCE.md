# EMAIL_REFERENCE.md

## Purpose

`email` contains mechanics created by the inbox and sequence surface: inbox entry, message-state design, body/readability constraints, design/linking choices, campaigns vs triggered flows, lifecycle branching, segmentation/cadence, and email-specific measurement.

## Canonical boundaries

- General copy, hooks, proof, storytelling, value communication, CTA psychology, and ideation stay in their general craft packs.
- Offer construction stays in `offer_framing`.
- Funnel states and cross-channel routing stay in `funnel_mechanics`; this pack owns how email expresses those states.
- Qualification criteria stay in `qualification`.
- Live objection handling and closing stay in `sales_conversations`.
- Deliverability infrastructure, sender authentication, provider rules, spam-filter tactics, legal consent/unsubscribe requirements, and platform-specific implementation stay in future `channel_ops` and must be re-checked when used.
- Cold-email infrastructure and mass-outbound tactics are not treated as durable email-format craft.

## Durable model

**recipient state → inbox entry → one message job → relevant action/state change → coordinated follow-up → downstream measurement**

## Explicit non-rules

The corpus contains many fixed prescriptions that were not promoted into durable rules, including:

- one universal subject-line length or capitalization style
- emojis always increase opens
- plain-text always beats designed email
- short email always beats long email
- one universal number of welcome emails
- one universal send frequency or day/time
- more segmentation is automatically better
- every sequence should push a discount
- open rate is the main success metric
- every subscriber should receive every campaign while inside every flow

## Date-sensitive material excluded

Authentication requirements (SPF/DKIM/DMARC), Gmail/Yahoo bulk-sender rules, Apple Mail behavior, provider-specific deliverability benchmarks, Klaviyo/Beehiiv/HubSpot implementation details, one-click unsubscribe mechanics, and current anti-spam/legal requirements must be verified at use time.
