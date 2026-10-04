"""Short-form motion-video engine: canonical VideoSpec schema + planner + compile + QC.

Slice 3/4 of the motion-engine roadmap (``docs/MOTION_ENGINE.md``). The numeric
``VideoSpec`` JSON contract is canonical here; ZEUS's renderer mirrors it in
zod at ``services/media_render/src/spec_schema.ts`` (never silently diverge).
"""
