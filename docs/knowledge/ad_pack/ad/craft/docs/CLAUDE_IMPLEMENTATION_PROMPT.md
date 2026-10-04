# Claude Code implementation prompt — KLEOS architecture expansion

You are working inside my OLYMPUS/ZEUS/KLEOS codebase. I am giving you a ZIP containing the canonical KLEOS knowledge library after a research expansion.

Your job is to integrate it **safely, completely, and with regression protection**. Do not merely copy folders and stop.

## Goal

Upgrade KLEOS from a mostly content/marketing library into the knowledge architecture below while preserving all existing behavior and data:

- `craft/`
- `formats/`
- `assets/`
- `business_mechanics/`
- `distribution/`
- `intelligence/`
- `growth/`
- `delivery/`
- `economics/`
- `strategy/`
- `ai_systems/`

The supplied ZIP is the canonical source for pack contents and folder ownership.

## New packs to integrate

### intelligence
- customer_research
- positioning
- market_intelligence
- experimentation

### growth
- outbound_acquisition
- crm_lifecycle
- paid_media
- seo_search_demand
- reputation_reviews

### delivery
- customer_onboarding
- service_delivery
- retention_expansion
- productization

### economics
- pricing (migrated from `business_mechanics/pricing`)
- unit_economics

### strategy
- brand_strategy
- decision_making

### ai_systems
- core pack `ai_systems` covering task decomposition, model routing, orchestration, reliability, latency/cost, evals/QC, retrieval/context, data pipelines, observability, tool orchestration, human-in-the-loop, security/permissions, provenance/versioning, automation design, and controlled feedback/self-improvement.

## Critical architectural rules

1. **One principle = one canonical home.** Do not duplicate rules across packs for convenience. Cross-reference the owning pack when needed.
2. Choose ownership by the **underlying mechanism**, not the surface where it appears.
   - proof in an ad → `craft/proof`
   - ad format mechanics → `formats/ad_creative`
   - auction/budget/media-buying mechanics → `growth/paid_media`
3. `pricing` now canonically lives at `kleos/economics/pricing/essentials.yaml`. Preserve `pack: pricing`. Remove the old duplicate path. If existing code depends on the old path, implement a temporary compatibility mapping in code rather than maintaining two files.
4. Platform-specific volatile knowledge must remain distinguishable from durable principles. Do not silently convert date-sensitive operational guidance into timeless rules.
5. Preserve provenance fields exactly. Existing `C12K:` sources and new `WEB:` sources are part of the knowledge data.

## Implementation tasks

### 1. Inspect before modifying
- Find every KLEOS loader, registry, glob, schema validator, pack router, context builder, cache, index, test, CLI, API, and documentation reference that assumes the old folder set.
- Identify hard-coded branch names and path assumptions.
- Identify whether packs are discovered recursively or from a static registry.

### 2. Integrate the canonical library
- Import all supplied pack YAMLs and reference files.
- Preserve all old packs and their contents unless the supplied library explicitly migrates them.
- Apply the `pricing` path migration exactly once.
- Do not create empty placeholder packs.

### 3. Make discovery architecture-agnostic
Prefer recursive pack discovery from `kleos/**/essentials.yaml` with schema validation over a hard-coded list of branches.
If a registry is necessary, generate or validate it from the filesystem so new branches do not require silent manual wiring.

Each loaded pack should expose at minimum:
- `schema_version`
- `pack`
- `kind`
- `title`
- categories/rules
- canonical path
- provenance/source fields

Reject duplicate `pack` identifiers at startup/build time.

### 4. Routing / retrieval
Update KLEOS retrieval/routing so the new branches are searchable and selectable.
Do not load all ~knowledge into every prompt. Retrieve the smallest relevant set of packs/rules for the task.
Support cross-domain retrieval when a task genuinely spans domains, but deduplicate by canonical rule identity/text.

Add/maintain boundaries so, for example:
- `customer_research` ≠ `market_intelligence`
- `positioning` ≠ `brand_strategy`
- `paid_media` ≠ `ad_creative`
- `unit_economics` ≠ `pricing`
- `customer_onboarding` ≠ `service_delivery`
- `retention_expansion` ≠ `crm_lifecycle`
- `ai_systems` guides ZEUS execution architecture, not business-domain advice.

### 5. Use `ai_systems` as ZEUS engineering knowledge
Wire the AI-systems pack into the places where ZEUS plans or evaluates workflows.
It should influence architecture decisions such as:
- deterministic code vs LLM vs agent
- single call vs chain vs router vs parallel fan-out/fan-in vs dynamic orchestrator-workers
- cheap/small model vs stronger model + escalation
- batching and concurrency
- retries/backoff/idempotency/checkpointing
- eval gates and regression testing
- context/retrieval/provenance
- tool permissions and human approval
- tracing/cost/latency metrics

Do **not** turn these principles into an autonomous self-modifying production system. Changes to prompts/routing/workflows may be proposed automatically, but must pass evals and controlled rollout before promotion.

### 6. Backward compatibility / migration
- Search for references to `business_mechanics/pricing` and migrate them.
- If persisted metadata stores old canonical paths, add a one-way migration or compatibility resolver.
- Do not maintain duplicate knowledge files indefinitely.
- Preserve public interfaces unless changing them is necessary; document any intentional break.

### 7. QA and tests
Add or run tests that prove:
- every `essentials.yaml` parses
- every pack has required schema fields
- every pack ID is unique
- recursive discovery finds all branches and all packs
- no exact duplicate rule text exists across canonical packs
- pricing resolves to the new economics path
- old pricing references resolve during the migration window if compatibility is needed
- retrieval can return rules from each new branch
- provenance survives indexing/context generation
- caches/indexes invalidate when pack files change
- malformed packs fail loudly rather than being skipped

Also run existing ZEUS/KLEOS tests and fix regressions caused by the migration.

### 8. Performance
Do not make KLEOS slower just because it contains more packs.
- cache parsed pack metadata by content hash/mtime
- build indexes once, incrementally when possible
- avoid reparsing every YAML for every request
- retrieve top relevant packs/rules instead of concatenating the library
- parallelize independent retrieval/index work where safe
- record retrieval latency and context size

### 9. Deliverables
When finished, give me:
1. concise summary of architecture changes
2. exact files changed
3. migration decisions
4. tests run + results
5. pack count and rule count discovered by the actual application
6. any remaining risks or TODOs
7. evidence that a representative query can retrieve from each new top-level branch

## Important constraints

- Do not rewrite the supplied knowledge because you personally prefer different phrasing.
- Do not invent sources.
- Do not duplicate migrated content.
- Do not overengineer with a new framework unless the existing architecture truly requires it.
- Prefer simple, deterministic, inspectable code.
- Before declaring success, run the code/tests and verify the actual loader sees the entire expanded library.
