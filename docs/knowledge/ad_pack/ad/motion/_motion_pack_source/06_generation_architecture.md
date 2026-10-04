# 06 — Generation Architecture

## Recommended architecture

```text
INPUT
(topic, script, brand kit, assets, duration, platform)
      ↓
CONTENT PLANNER
(narrative beats + evidence requirements)
      ↓
FORMAT SELECTOR / FORMAT CREATOR
(existing grammar or mutated new grammar)
      ↓
ART DIRECTOR
(palette, type, material, density, signature mechanic)
      ↓
SCENE GRAPH GENERATOR
(objects, relationships, states, bridges)
      ↓
ASSET PIPELINE
(text, icons, screenshots, static images, logos, diagrams)
      ↓
MOTION COMPILER
(scene graph -> deterministic primitives/keyframes)
      ↓
RENDERER
(Remotion / SVG / Canvas / WebGL / optional Blender)
      ↓
QC
(readability, clipping, continuity, pacing, brand consistency)
      ↓
VARIANTS
      ↓
EXPORT
```

---

# 1. LLM responsibilities

Use LLMs for:
- script decomposition
- selecting visual metaphors
- choosing format family
- defining scene roles
- generating semantic object graph
- proposing novelty mutations
- choosing evidence
- critiquing compositions

Do **not** rely on LLMs to manually emit raw frame-by-frame keyframes.

---

# 2. Deterministic engine responsibilities

Use code for:
- layout
- spacing
- timing
- interpolation
- masks
- typography
- transitions
- layer ordering
- screen capture insertion
- responsive safe zones
- collision detection
- rendering

This is where reliability comes from.

---

# 3. Recommended renderer stack

## Primary: Remotion + React/SVG/Canvas
Best for:
- text
- cards
- UI
- screenshots
- diagrams
- 2D and light 2.5D

## Optional: WebGL / Three.js
Use for:
- depth-heavy cards
- procedural fields
- complex particles
- 3D camera choreography

## Optional: Blender
Use selectively for:
- true 3D product/object scenes
- advanced geometry

Do not make Blender mandatory for standard reels.

---

# 4. Data model

Store videos as:

```text
project
  content_spec
  art_direction
  format_spec
  scenes[]
    semantic_role
    objects[]
    relations[]
    initial_state
    events[]
    final_state
    bridge
  audio_timeline
  qc_report
```

This enables editing and regeneration without prompting the entire video again.

---

# 5. Asset generation policy

Priority order:
1. existing authentic assets
2. screenshots / product/UI assets
3. icons / vectors / procedural shapes
4. static image generation
5. generative video only when unavoidable

For this motion-graphics system, generated moving humans should not be a dependency.

---

# 6. Reusability system

Separate:

## Format grammar
Reusable across topics.

## Brand skin
Palette, typefaces, logo, texture, radius, stroke.

## Content payload
Topic, words, data, screenshots, examples.

This lets one format create hundreds of visibly distinct videos.

---

# 7. Rendering strategy

The system should support:
- preview render at low resolution
- QC pass
- corrected render
- final high-resolution export

Do not spend full render cost before layout/timing checks pass.

---

# 8. Format discovery mode

A separate R&D process should:
1. sample 2–3 existing grammars
2. mutate them
3. generate 5–8s prototypes
4. rank prototypes
5. save successful new format specs

New formats should graduate into the production library only after passing evaluation.
