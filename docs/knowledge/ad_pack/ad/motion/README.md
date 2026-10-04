# Motion-graphics knowledge (KLEOS area)

Engine-level knowledge for producing **short-form motion-graphics videos**
(typography, cards, diagrams, kinetic type, editorial grids, scrapbook, UI
tutorials, …) with deterministic, code-driven rendering. Reusable by any
business pack that runs short-form video; it contains **no business specifics**.

## Source

Distilled from a 49-reel reverse-engineering batch. The **14 source documents**
are kept verbatim under [`_motion_pack_source/`](_motion_pack_source/) as
provenance. Every rule in these packs carries a `source` tag of the form
`MP:<file>#<section>` pointing back into that folder.

The design philosophy, captured in the packs: references are evidence for
**reusable design grammar**, never templates to clone. The system invents new,
coherent formats by mutating dimensions (layout/motion/material/timing/…) at a
chosen creativity level, and rejects slop with deterministic QC before a human
ever sees it.

## Packs

| Pack | kind | Covers | Source doc(s) |
|---|---|---|---|
| `motion_principles` | motion | design constraints, continuity, density, semantic motion, automation tiers, visual hooks | 01, 12 |
| `motion_formats` | motion_format | the 16 reusable format families (F01–F16) as grammars | 02 |
| `motion_primitives` | motion | transform / group / reveal / transition / typography / diagram / UI / collage / abstract / timing / easing vocabulary | 03 |
| `motion_scene_grammar` | motion | scene roles, object model, readability, chaining, bridges, rhythm, density | 04 |
| `motion_mutation` | motion | mutation dimensions, operators, hybridization, signature mechanic, distance score, creativity modes | 05 |
| `motion_qc` | motion | hard rejections, 100-pt rubric, production threshold, slop failure modes, automated checks | 07 |
| `motion_learning` | motion | generation log, craft vs topic, metrics, review labels, promotion lifecycle, compatibility | 09 |
| `motion_architecture` | motion | layered pipeline, LLM vs deterministic split, renderer stack, data model, reuse, preview-then-final | 06, 10 |

## How it is consumed

Kinds are deliberately **not** `general` or `format`, so these packs never
auto-leak into copy drafting (`select_craft_brief` pools only `kind: general`).
They are reached explicitly by the video planner when it needs craft context,
via `craft_compose([...])` or `retrieve_brief(branch='motion')`.

## Where the numbers live

Prose grammar lives here in these packs. **Machine-structured spec YAML and the
typed pydantic schemas** (FormatSpec, SceneSpec, VideoSpec, QCReport) live under
`kleos/core/motion/` — the code gear that plans and QC's videos. Keep prose in
this area, keep numbers in the code gear.
