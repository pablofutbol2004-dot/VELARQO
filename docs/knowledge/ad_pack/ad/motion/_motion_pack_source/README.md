# Motion Graphics Reverse-Engineering Pack

Source batch: `seis.motion_DcojE7gvA8t_00001.zip` — 49 reference videos.

Goal:
1. Make an AI system able to generate motion-graphics videos in these families repeatedly and reliably.
2. Make the system able to invent **new, coherent formats** instead of cloning references.

This pack treats references as evidence for reusable design grammar, not as templates to copy literally.

## Files

- `01_master_analysis.md` — major findings and design principles from the batch.
- `02_format_library.md` — reusable motion-video format families distilled from the references.
- `03_motion_primitives.md` — low-level motion, composition, typography and transition primitives.
- `04_scene_grammar.md` — how to assemble primitives into scenes and videos.
- `05_creative_mutation_engine.md` — system for generating genuinely new formats.
- `06_generation_architecture.md` — recommended AI + deterministic rendering architecture.
- `07_quality_control.md` — anti-slop QC rules, scoring and rejection criteria.
- `08_format_spec_schema.md` — machine-readable schema for storing formats.
- `09_eval_and_learning_loop.md` — how the system should learn from outputs and performance.
- `10_implementation_prompt_for_claude.md` — implementation brief for a coding agent.
- `11_source_index.md` — reference videos and the main mechanic each contributes.
- `12_content_creation_knowledge.md` — content/storytelling lessons visible in this motion batch.
- `13_business_knowledge.md` — business knowledge visible in the batch where defensible.

## Central recommendation

Do **not** build a monolithic prompt-to-video agent.

Build a layered system:

`content plan -> narrative beats -> format grammar -> scene graph -> motion primitives -> deterministic renderer -> QC -> variations`

Use AI mainly for planning, design decisions, asset generation/selection and mutation. Use code for timing, layout, interpolation, masking, typography, compositing and final rendering whenever possible.
