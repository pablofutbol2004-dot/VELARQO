# Instagram Carousel Analysis Pack

## Scope

This pack analyzes the supplied Instagram carousel corpus as a **generation problem**, not as an inspiration board.

Corpus inspected:
- 50 carousels from the main archive.
- 4 additional carousels from the addendum.
- 54 carousels total.
- 469 slide files in the extracted archives, including a small number of video slides.

The analysis has two separate layers:

1. **Carousel craft** — what the posts actually do: cover construction, slide roles, sequencing, swipe logic, visual hierarchy, layout, typography, imagery, rhythm, proof, CTAs, and failure modes.
2. **Embedded knowledge** — useful ideas taught inside some carousels about content, storytelling, branding, design, marketing, business, and creative work.

The goal is to give an AI system enough structure to:
- create strong carousels repeatedly;
- choose a format appropriate to the content rather than force every idea into one template;
- invent new combinations and visual treatments;
- understand why a carousel works;
- reject weak output through explicit QC.

## Evidence labels

The corpus contains strong work, weak work, stylistic preferences, and creator claims presented as universal rules. They are not treated equally.

- **CORE** — repeated across substantially different examples and useful as a general design/generation rule.
- **STRONG INFERENCE** — not literally stated by the corpus, but strongly supported by repeated observed behavior.
- **OPTIONAL / STYLE** — a useful device that should remain selectable, not mandatory.
- **SOURCE CLAIM** — advice explicitly stated by a creator, but not established by this corpus alone.
- **CONFLICT / OVERGENERALIZATION** — advice that becomes misleading if converted into a universal rule.

## Important synthesis

A major apparent contradiction in the corpus is:

- “Every slide should work as a screenshot on its own.”
- “Every slide should make the next swipe necessary.”

The stronger synthesis is:

> **Local completeness + global incompleteness.**

A strong slide should usually be understandable and valuable in isolation, while the sequence still contains unresolved value, progression, contrast, or payoff that makes continuing desirable.

This is more useful for generation than either absolute rule.

## Files

- `CAROUSEL_CRAFT_SYSTEM.md` — the core operating model.
- `ARCHETYPES_AND_SEQUENCE_BLUEPRINTS.md` — reusable carousel architectures and slide-role patterns.
- `HOOKS_COVERS_AND_SWIPE.md` — cover mechanics, hook families, slide-2 behavior, and continuation devices.
- `VISUAL_GRAMMAR_AND_LAYOUTS.md` — visual hierarchy, typography, image logic, layout primitives, rhythm, and composition.
- `AI_GENERATION_AND_NOVELTY_SPEC.md` — a machine-oriented generation process designed to avoid template cloning.
- `QC_RUBRIC_AND_FAILURE_MODES.md` — explicit acceptance tests and common failure modes.
- `META_KNOWLEDGE_EXTRACTED.md` — useful content/business/design knowledge taught inside the source carousels, with caveats.
- `CORPUS_NOTES.md` — concise traceability notes for all 54 source carousels.
- `corpus_inventory.csv` — structured source inventory with derived classifications.

## How to use this pack in KLEOS / ZEUS

Do **not** load all files into every generation prompt.

Recommended split:
- planner: `CAROUSEL_CRAFT_SYSTEM.md` + `ARCHETYPES_AND_SEQUENCE_BLUEPRINTS.md`;
- cover planner: `HOOKS_COVERS_AND_SWIPE.md`;
- art/layout planner: `VISUAL_GRAMMAR_AND_LAYOUTS.md`;
- generator/orchestrator: `AI_GENERATION_AND_NOVELTY_SPEC.md`;
- critic/QC: `QC_RUBRIC_AND_FAILURE_MODES.md`;
- optional knowledge/reference retrieval: `META_KNOWLEDGE_EXTRACTED.md` and `CORPUS_NOTES.md`.

This keeps generation deterministic enough to be reliable while preserving variation.
