# Velarqo — HighLevel documentation pack

Updated: 2026-09-27

Purpose: give coding agents working on Velarqo a reliable map of GoHighLevel/HighLevel (GHL) features, product documentation, API documentation, webhooks, auth, and official SDKs.

## What is included

- `AGENTS_GHL.md` — instructions for Claude Code / Codex / Cursor agents.
- `VELARQO_PRIORITY.md` — which parts matter most for a home-services automation business.
- `GHL_FOR_VELARQO.md` — translation layer: Velarqo concepts ↔ GHL implementation, with pointers into this repo's actual code.
- `api/` — developer/API-surface docs:
  - `API_MAP.md` — API surfaces, v2/v3 notes, official repos.
  - `AUTH.md` — Private Integration Token vs OAuth 2.0, token lifetimes, scopes.
  - `RATE_LIMITS.md` — burst/daily limits and what they mean for batching/queueing.
  - `WEBHOOKS.md` — event families, idempotency/ordering rules, where they plug into this repo.
  - `CHANGELOG.md` — pointer to the live API changelog (not a mirror — it drifts).
  - `official-docs/` — synced official `highlevel-api-docs` repo (OpenAPI/Markdown).
  - `sdk/` — synced official `highlevel-api-sdk` repo.
- `product/` — feature-area docs (`FEATURE_MAP.md` plus one file per Tier 1 area: contacts, opportunities, conversations, calendars, workflows, snapshots), each mapping onto this repo's schemas/modules.
- `communications/` — deliverability and compliance: email domains/verification/deliverability, SMS compliance, phone.
- `sources/` — `SOURCES.yaml` (machine-readable registry), `SUPPORT_PORTAL_INDEX.md` (UI/product behavior), `PRODUCT_CHANGELOG.md` (pointer to the live product changelog).
- `scripts/sync-ghl-docs.ps1` / `.sh` — sync script for the official API docs + SDK repos into `api/official-docs/` and `api/sdk/`.

## First setup

This folder already lives at `docs/ghl/` in the Velarqo repo. To (re)sync the
official API docs + SDK:

```powershell
powershell -ExecutionPolicy Bypass -File .\docs\ghl\scripts\sync-ghl-docs.ps1
```

This clones/updates HighLevel's official API docs into `api/official-docs/`
and the SDK into `api/sdk/`.

## Source-of-truth policy

1. For API schemas/endpoints, prefer the local official `api/official-docs/` repo after sync.
2. For current UI behavior and feature configuration, use the official Support Portal links in `sources/SUPPORT_PORTAL_INDEX.md`.
3. For authentication, scopes, webhooks, and Marketplace apps, prefer the current Developer Portal (`api/AUTH.md`, `api/WEBHOOKS.md`).
4. Do not rely on old v1 examples. HighLevel marks v1 end-of-support as 2025-12-31.
5. Check version headers and docs version before implementing; HighLevel is actively adding v3 endpoints.
6. For "did this change recently," check `api/CHANGELOG.md` (API) or `sources/PRODUCT_CHANGELOG.md` (product/UI) before trusting a doc frozen at sync/write time.
7. For "how does this map onto Velarqo's actual code," start at `GHL_FOR_VELARQO.md`, not the raw API docs.

## Why the Support Portal is not copied wholesale

HighLevel's Support Portal is large and changes continuously. This pack stores a canonical index instead of a stale mirror. The API docs are different: HighLevel publishes their source as a public GitHub repository, so the sync scripts vendor that machine-readable material directly.
