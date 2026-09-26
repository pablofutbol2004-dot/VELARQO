# HighLevel API map

## Canonical developer sources

- Developer/API portal: https://marketplace.gohighlevel.com/docs/
- Official public API docs repository: https://github.com/GoHighLevel/highlevel-api-docs
- Official TypeScript/JavaScript SDK: https://github.com/GoHighLevel/highlevel-api-sdk
- Official PHP SDK: https://github.com/GoHighLevel/highlevel-api-php
- Developer landing page: https://developers.gohighlevel.com/

## Authentication

HighLevel documents two main integration patterns:

- **Private Integration Token** — best fit for internal tools / controlled accounts.
- **OAuth 2.0 Authorization Code flow** — for Marketplace/public apps and delegated multi-account access.

Developer docs: https://marketplace.gohighlevel.com/docs/Authorization/OAuth2.0/
Scopes: https://marketplace.gohighlevel.com/docs/Authorization/Scopes/

## Rate limits

Official help documentation currently states for public v2 OAuth APIs:

- burst: 100 requests per 10 seconds per Marketplace app per resource
- daily: 200,000 requests per day per Marketplace app per resource

Treat these as version/plan-sensitive and re-check before production rollout.

## API versioning

- API v1 reached end-of-support on 2025-12-31.
- The Developer Portal supports versioned references.
- The official GitHub repo contains classic specs plus a growing `apps/v3/` tree.
- Always inspect the `Version` header / selected API version for the endpoint you implement.

## Major API surfaces currently present in the official repository

CRM & data:
- Contacts
- Businesses
- Companies
- Objects / custom objects
- Associations
- Custom fields
- Users
- Sub-accounts / locations
- Tasks / notes via relevant APIs

Sales & lifecycle:
- Opportunities / pipelines
- Calendars / appointments
- Campaigns
- Workflows (note: public workflow API coverage is not equivalent to the full UI workflow builder)
- Trigger links

Communications:
- Conversations
- Email / LC Email
- Phone system
- Chat widget (v3)
- Conversation AI
- Voice AI

Marketing/content:
- Forms
- Surveys
- Funnels
- Blogs
- Social Planner / social posting
- Ad publishing / Ad Manager
- Brand boards
- Knowledge base
- Media library

Commerce:
- Payments
- Products
- Invoices
- Store
- Proposals / documents
- Affiliate manager

Agency/platform:
- Marketplace
- SaaS API
- Snapshots
- Custom menus
- Agent Studio

## Webhooks

Canonical webhook category:
https://marketplace.gohighlevel.com/docs/category/webhook/

Important Velarqo event families include:

- contacts: create/update/delete, DND, tags
- appointments: create/update/delete
- opportunities: create/update/delete, stage/status/assignee/monetary value
- conversations/messages: inbound/outbound/unread/conversation updates
- tasks/notes
- invoices/orders/payments-related events
- users/locations
- product/price events
- custom object schema/record/association events
- app install/uninstall/update/payment status

Design integrations event-first where possible, but make webhook handling idempotent and resilient to retries/out-of-order delivery.

## Local vendoring

Run `scripts/sync-ghl-docs.ps1` (Windows) or `scripts/sync-ghl-docs.sh` to pull the current official API docs + SDK into `vendor/`.
