# 10 — Implementation Prompt for Claude / Coding Agent

You are implementing a production-grade **AI motion-graphics video system** inspired by the accompanying reverse-engineering pack.

Read all files in this directory before coding.

## Objective
Build a system that can:

1. generate high-quality short-form motion-graphics videos repeatedly from a content brief;
2. reproduce broad format families without hardcoding exact reference videos;
3. create new coherent formats through controlled mutation;
4. render deterministically whenever possible;
5. reject low-quality / inconsistent outputs before final rendering.

## Architectural requirements

Use a layered architecture:

```text
brief
-> content planner
-> format selector / mutation engine
-> art direction
-> scene graph
-> asset resolver
-> motion compiler
-> renderer
-> automated QC
-> preview
-> final render
```

Do NOT build one giant prompt that returns a finished video specification.

## Renderer
Prefer:
- React + Remotion
- SVG/HTML/CSS/Canvas for 2D
- optional Three.js/WebGL for advanced 2.5D/3D primitives

Avoid making Blender or generative video mandatory.

## Core implementation requirement
Implement a reusable primitive system for:

### transforms
translate, scale, rotate, orbit, parallax, camera pan/zoom

### groups
fan, stack, grid, rail, radial, stagger, cascade

### reveals
mask, crop, clip, line draw, type-on, blur/focus

### transitions
match-move, card-to-fullscreen, crop-to-scene, wipe, push, hard cut

### typography
keyword isolate, tracking changes, line reveals, highlight, counter

### diagrams
nodes, edges, branches, timelines, funnels, comparisons

### UI
cursor, click, panel expand, zoom-to-control, callout

### collage
paper, tape, sticker, photo drop, rip mask, jitter

## Structured specs
Use explicit schemas for:
- `FormatSpec`
- `SceneSpec`
- `ObjectSpec`
- `MotionEvent`
- `ArtDirection`
- `QCReport`

Use JSON/YAML validation. Invalid specs must fail loudly before rendering.

## Scene model
Every scene must have:
- semantic role
- semantic goal
- attention target
- object list
- initial state
- motion events
- final state
- transition bridge

## Format library
Implement the format families documented in `02_format_library.md` as reusable grammars, starting with:

1. F01 Kinetic Card Constellation
2. F02 Progressive Diagram Explainer
3. F03 Kinetic Type Argument
4. F04 Editorial Grid Story
5. F06 Screen-in-Scene Tutorial
6. F07 Scrapbook Knowledge Reel
7. F13 App/System Architecture Map
8. F14 Single-Canvas Visual Metaphor

Do not implement all formats at once if that harms reliability. Build the primitives first and prove 2–3 formats end-to-end.

## Creativity engine
Implement controlled mutation over:
- layout topology
- motion topology
- material language
- typography behavior
- temporal rhythm
- narrative topology

Each mutation should be explicit and logged.

A `mutation_mode` should support:
- conservative
- exploratory
- experimental

Do not allow random changes to every dimension simultaneously.

## QC
Implement deterministic checks for:
- bounds/safe zones
- minimum font size
- object collisions
- text screen-time
- font count
- palette count
- transition-family count
- motion spikes

Provide extension points for vision-model critique later.

## Preview pipeline
Before expensive final rendering:
1. render low-res preview
2. run QC
3. revise spec if necessary
4. render final

## Non-negotiable quality principles
- motion must have semantic purpose
- one focal target per moment
- continuity across scenes
- consistent design system
- no random effects
- no “static poster + zoom” as default animation
- avoid generative moving humans
- use authentic/screens/static assets before generative video

## Testing
Build tests for:
- schema validation
- primitive interpolation
- deterministic rendering from same seed/spec
- safe zones
- collision detection
- format compilation
- mutation reproducibility

Create visual regression snapshots for representative scenes.

## Deliverable sequence

### Phase 1
- schemas
- primitive engine
- renderer skeleton
- test harness

### Phase 2
- F01 + F02 + F03
- preview renderer
- QC

### Phase 3
- mutation engine
- additional formats
- format creation workflow

### Phase 4
- performance logging
- learning/evaluation loop

At the end, provide:
- architecture docs
- file tree
- run commands
- example briefs
- example generated specs
- test results
- known limitations
