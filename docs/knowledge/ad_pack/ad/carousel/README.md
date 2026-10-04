# Carousel knowledge (KLEOS area)

Engine-level knowledge for producing **Instagram/feed carousels** (cover, slide
roles, sequencing, swipe logic, visual hierarchy, layout, typography, QC) with
deterministic code-driven rendering. Reusable by any business pack that runs
carousels; no business specifics live here.

## Source

Distilled from a **54-carousel reverse-engineering batch** (reverse-engineered
like the motion pack). The **8 source documents** are kept verbatim under
[`_carousel_pack_source/`](_carousel_pack_source/) as provenance; rules carry
`source` tags `CP:<FILE>#<section>` pointing back into that folder. The two
knowledge packs (motion + carousel) share the same philosophy: references are
evidence for **reusable grammar**, never clone templates.

## Packs

| Pack | kind | Covers | Source doc |
|---|---|---|---|
| `carousel_craft` | carousel | what a carousel is, local-completeness law, slide jobs, cover as acquisition, progression, compression, rhythm, invariants, production loop | CAROUSEL_CRAFT_SYSTEM |
| `carousel_visual_grammar` | carousel | invariants/variables, hierarchy, type roles, alignment, spacing scale, grids, image roles, before/after, repetition, whitespace, color, diagrams, continuity, rhythm plan | VISUAL_GRAMMAR_AND_LAYOUTS |
| `carousel_qc` | carousel | 0–5 rubric + gates, reject-when rules, anti-template + contact-sheet tests, failure modes | QC_RUBRIC_AND_FAILURE_MODES |
| `carousel_covers` | carousel | cover objective, hook families, visual hook mechanisms, layout primitives, feed-size + contextless tests, slide-2 bridge | HOOKS_COVERS_AND_SWIPE |
| `carousel_archetypes` | carousel | 12 reusable archetypes + blueprints, sequence primitives, choosing rule, hybrids | ARCHETYPES_AND_SEQUENCE_BLUEPRINTS |
| `carousel_generation` | carousel | required inputs, planner output, viewer-change, cover ×3, sequence curve, novelty engine, evidence integrity, render loop | AI_GENERATION_AND_NOVELTY_SPEC |
| `carousel_meta_knowledge` | carousel | business-job, hooks/attention, storytelling, voice/brand, positioning, authority (with confidence framing) | META_KNOWLEDGE_EXTRACTED |

## How it is consumed

Kinds are **not** `general`/`format`, so these packs never auto-leak into copy
drafting. Reach them explicitly via `craft_compose([...])` or
`retrieve_brief(branch='carousel')` — the cover/visual/QC roles map to the
pack's categories. The deterministic frame renderer
(`D:\ZEUS\services\media_render`) turns slide plans into stills/MP4s.
