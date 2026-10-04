# KLEOS craft knowledge

Engine-level, general know-how for producing content well. Never a business
pack's knowledge: a business pack decides which formats it runs and draws on
whatever craft applies; nothing here contains business specifics.

## Library areas

Packs live under sibling areas of the knowledge root (`kleos/`). Discovery is
recursive and keyed by the pack's declared `pack` id (not its folder name): any
`<area>/<pack>/essentials.yaml` is found automatically, so a new area needs no
code wiring. `kleos.craft.load_craft_pack` / `discover_library` / `validate_library`
are the single loader entry points.

- `kleos/craft/` — general (format-agnostic) packs (`kind: general`); legacy
  format pack `short_form_video` lives here (newer format packs use `formats/`).
- `kleos/business_mechanics/` — reusable business mechanics (kind
  `business_mechanics`): `offer_framing` (offer definition/framing and
  price/term communication), `funnel_mechanics` (path length, destinations,
  state transitions, attribution as re-check), `qualification` (criteria,
  evidence, fit/readiness, scoring, routing, calibration) and
  `sales_conversations` (interactive framing, discovery, objection
  clarification, proof in dialogue, decision/close, follow-up, call review).
  These feed Offer/Conversion/Qualification/sales decisions, not content
  drafting.
- `kleos/formats/` — literal format packs (kind `format`): landing_page, vsl,
  webinar, email, long_form_video, carousel, written_post, ad_creative.
- `kleos/assets/` — asset-class packs (kind `asset_class`), e.g. `lead_magnet`
  (an opt-in asset class that is not a single medium).
- `kleos/distribution/` — how content reaches people through channels/people.
  `distribution_through_people` (kind `distribution`) covers people-powered
  reach; `channel_ops` (kind `distribution_ops`, flagged high volatility —
  re-check platform mechanics before use). These need their own consumers and
  are not part of a draft/format bundle.
- `kleos/economics/` — pricing economics (kind `economics`): `pricing`
  (canonical home of pricing after its move from `business_mechanics/pricing`;
  pack id unchanged) and `unit_economics`.
- `kleos/intelligence/` — market understanding (kind `intelligence`):
  `customer_research`, `positioning`, `market_intelligence`, `experimentation`.
- `kleos/growth/` — acquisition mechanics (kind `growth`): `outbound_acquisition`,
  `crm_lifecycle`, `paid_media`, `seo_search_demand`, `reputation_reviews`
  (platform-dependent parts of `channel_ops`, `paid_media`, `seo_search_demand`
  and `reputation_reviews` are date-sensitive — re-verify before use).
- `kleos/delivery/` — delivering what you sell (kind `delivery`):
  `customer_onboarding`, `service_delivery`, `retention_expansion`,
  `productization`.
- `kleos/strategy/` — strategy (kind `strategy`): `brand_strategy`,
  `decision_making`.
- `kleos/motion/` — motion-graphics design grammar for deterministic, code-driven
  short-form video (kind `motion` / `motion_format`): `motion_principles`,
  `motion_formats` (F01–F16), `motion_primitives`, `motion_scene_grammar`,
  `motion_mutation`, `motion_qc`, `motion_learning`, `motion_architecture`.
  Consumed explicitly by the video planner (see `kleos/motion/README.md`), never
  auto-leaked into copy drafting.
- `kleos/carousel/` — carousel design grammar for deterministic feed-slide
  production (kind `carousel`): `carousel_craft`, `carousel_covers`,
  `carousel_visual_grammar`, `carousel_qc` (+ more packs in a later pass). See
  `kleos/carousel/README.md`; never auto-leaked into copy drafting.
- `kleos/ai_systems/` — ZEUS engineering knowledge (kind `ai_systems`): the
  `core` pack (at `ai_systems/core/`) covers how to design, route, execute,
  validate, observe, secure and improve AI/automation workflows. Consult it
  (via `craft_brief("ai_systems", ...)`, `retrieve_brief`, or
  `python -m kleos ask ... --branch ai_systems`) when planning or evaluating an
  execution workflow. It informs architecture decisions (deterministic code vs
  LLM vs agent, single call vs chain vs orchestrator, model routing/escalation,
  retries/idempotency/checkpointing, eval gates, context/provenance, tool
  permissions/human approval, tracing/cost/latency) — it must guide decisions,
  never auto-apply them as an autonomous self-modifying system.

Ownership is by the underlying mechanism, not the surface where a rule appears:
proof inside an ad lives in `craft/proof`; the ad FORMAT lives in
`formats/ad_creative`; auction/budget mechanics live in `growth/paid_media`.

## Package map

Two kinds of pack, flat under `kleos/craft/<pack>/` (each holds `essentials.yaml`
plus a reference map; the loader is `kleos.craft.load_craft_pack` /
`craft_brief` / `craft_compose`).

**GENERAL thematic packs (`kind: general`) — format-agnostic principles:**

| Pack | What belongs there |
|---|---|
| `attention` | relevance, curiosity, pattern interruption, cognitive load, open questions, maintaining attention |
| `hooks` | hook mechanisms, promises, stakes, specificity, contrast, novelty, hook sequences |
| `storytelling` | tension, setup/payoff, escalation, open loops, narrative arcs, information sequencing |
| `copywriting` | clarity, compression, specificity, sentence construction, persuasion, word economy |
| `spoken_writing` | conversational language, cadence, breath/beat length, writing for ears not eyes |
| `value_communication` | explaining useful ideas, completeness vs breadth, proof, examples, making abstract ideas concrete |
| `visual_communication` | visual hierarchy, visual proof, text-image relationship, B-roll purpose, composition |
| `editing` | cuts, pacing, transitions, information density, rhythm, motivated editing, sound |
| `packaging` | titles, thumbnails/first frames, captions, framing, positioning an idea before consumption |
| `cta_conversion` | CTAs, next-step design, reducing friction, matching CTA to audience state |
| `content_quality` | generic vs distinctive, weak patterns, clarity failures, payoff failures, QC rules |
| `content_measurement` | retention, response signals, testing variables, diagnosing failure, iteration |
| `proof` | making claims credible: evidence/proof hierarchy, demonstrations, trust rules (general; passes kept in `docs/PASS_01_PROOF_*`) |
| `ideation_angles` | finding/selecting ideas and angles: idea mining, angle construction, remixing/reuse, novelty (feeds the Strategy/ideation step; pass-02 logs in `docs/PASS_02_*`) |

**FORMAT packs (`kind: format`) — medium-specific rules:**

| Pack | Notes |
|---|---|
| `short_form_video` | currently a FULL pack (predates the general split); keep until a second format consumer justifies pruning to format-specific rules |
| `long_form_video`, `carousel`, `written_post`, `email`, `ad`, … | future |

## How a piece loads craft

A piece composes the packs it needs — it does not expect one pack to teach
everything. Example: a short-form video might load
`hooks + storytelling + spoken_writing + value_communication + packaging +
cta_conversion + short_form_video` via `craft_compose([...])`, and the slice
passes the composed text as `craft_brief`.

## The no-duplication rule

An underlying principle lives in EXACTLY ONE general package; format packs only
add medium-specific contextual rules and never rediscover a general principle.
Example: "create an unanswered question early and delay its resolution" →
`attention`/`storytelling`. A short-form pack may add its contextual version
("apply it early because short-form viewers can leave instantly") but must not
restate the general principle.

## Authoring rules for a new pack (ChatGPT distillation)

- Complete coverage, not favorites; paraphrase into rules (never long verbatim,
  never embeddable media); examples described as patterns.
- Neutral and general — no industry/niche/account specifics.
- Tag provenance; when sources conflict keep both and note the conflict.
- Mark date-sensitive / platform-specific claims as "re-check".
- `essentials.yaml` rules are prescriptive one-liners with `why`; fields:
  `schema_version`, `pack`, `kind` (`general`|`format`|area kind such as
  `economics`/`growth`/`strategy`/`ai_systems`), `title`, `categories`.
- `short_form_video` predates this split; when a second format pack lands and
  overlap is real, prune it to format-specific rules + compose the general packs
  it needs (do not refactor preemptively).
