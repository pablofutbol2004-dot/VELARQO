# CHANNEL_OPS_REFERENCE.md

## Purpose

`channel_ops` contains operational knowledge for running distribution channels and messaging infrastructure: publishing cadence, profile surfaces, platform-native routing, social discovery mechanics, DM automation, WhatsApp operations, YouTube/LinkedIn/X/TikTok execution, email deliverability, safety, and channel-level diagnostics.

## Volatility contract

**This pack is high-volatility. Re-check before execution.**

The following are never treated as timeless without current verification:

- algorithm ranking claims
- exact post-frequency or best-time prescriptions
- hashtag/tag/keyword weighting
- account eligibility and verification requirements
- API endpoints, permissions, throughput, rate limits, quotas, or coexistence behavior
- WhatsApp messaging windows, template categories, outbound rules, and pricing
- email-provider thresholds and authentication requirements
- platform-specific automation permissions
- commerce/affiliate availability by country
- UI paths and tool-specific setup instructions

Store operational facts with an **as-of date + market/account context** when they are used in production.

## Canonical boundaries

- `distribution_through_people` owns referrals, partners, advocates, communities, and people-powered distribution.
- General craft packs own how communication is written/designed/persuades.
- Format packs own medium-specific execution such as carousels, email composition, YouTube long-form structure, ads, VSLs, and landing pages.
- Business-mechanics packs own downstream funnel state, qualification, offer, and sales conversations.
- `channel_ops` owns the operational constraints and current platform layer around those assets.

## Durable operating model

**channel objective → current platform constraints → account/profile state → publish/message action → platform signal → audience response → owned/downstream outcome → diagnosis → re-check + iteration**

## Explicit non-rules

- post N times per day on every account
- always post at a universal clock time
- use exactly N hashtags
- “the algorithm rewards X” forever
- a fixed CTR or retention benchmark defines a good YouTube video
- every Instagram CTA should be a comment-to-DM automation
- every business should use the direct WhatsApp Cloud API
- an official API permits unsolicited spam
- a fixed WhatsApp message quota or template price is permanent
- a fixed email open/complaint threshold is permanent
- more impressions always means better LinkedIn business performance
- more followers always means more TikTok Shop revenue
- tags/descriptions are always a major YouTube ranking lever
- one platform should be allowed to become a single point of failure
