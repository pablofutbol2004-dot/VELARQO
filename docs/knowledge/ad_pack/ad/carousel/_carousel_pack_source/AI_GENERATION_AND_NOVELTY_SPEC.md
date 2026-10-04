# AI Carousel Generation and Novelty Spec

## Goal

Build a system that can generate high-quality carousels repeatedly **without degenerating into template cloning**.

The system should treat a carousel as a planned sequence with:
- a viewer objective;
- an information architecture;
- a visual system;
- controlled variation;
- evidence/asset constraints;
- explicit QC.

---

# 1. Required inputs

Minimum inputs:

```yaml
objective: >
  What should change in the viewer after the carousel?
audience:
  who: "specific audience"
  current_state: "what they know/believe/do now"
  desired_state: "what they should know/believe/do after"
core_idea: "one-sentence thesis"
content_mode: auto | content_first | image_first | experience_first
cta:
  type: none | save | share | follow | comment_keyword | dm | click | book | visit | other
  action: "specific action"
brand:
  voice: "voice summary or voice-pack ref"
  visual_identity: "brand-system ref"
assets:
  available_images: []
  screenshots: []
  evidence: []
constraints:
  min_slides: 2
  max_slides: 15
  language: "..."
  platform: "Instagram"
```

Optional inputs:
- required facts;
- product/service;
- offer;
- season/local context;
- creator references;
- visual mood;
- proof sources;
- forbidden claims;
- forbidden styles;
- prior carousels to avoid repeating.

---

# 2. Planner output

The planner must output a structured plan **before writing final copy or generating images**.

```yaml
thesis: "..."
viewer_change: "..."
selected_archetype: "..."
why_this_archetype: "..."
sequence_engine:
  primary: "contrast | enumeration | narrative | escalation | reveal | proof | progression | visual-curiosity"
  secondary: "..."
cover:
  hook_family: "..."
  promise: "..."
  visual_concept: "..."
  layout_primitive: "..."
visual_invariants:
  - "..."
visual_variables:
  - "..."
slides:
  - index: 1
    role: cover
    core_idea: "..."
    reason_to_continue: "..."
    visual_function: "hero"
    dominant_element: "headline | image | diagram | screenshot"
    density: low
    continuity_device: "..."
    evidence_required: false
  - index: 2
    role: validation
    core_idea: "..."
    reason_to_continue: "..."
    visual_function: "..."
    dominant_element: "..."
    density: medium
    continuity_device: "..."
    evidence_required: false
```

No rendering until this plan passes structural QC.

---

# 3. Step-by-step generation pipeline

## Stage A — Define the viewer change

The system should complete:

> “The viewer currently ______. After the carousel, they should ______.”

Examples:
- thinks daily posting = marketing → understands message/audience/action alignment;
- does not know what makes a cover strong → can diagnose and construct one;
- sees a detailing service as generic → understands specific failure risks and why the service matters;
- knows a project visually → feels the atmosphere of living there.

If the transformation cannot be stated, the idea is not ready.

---

## Stage B — Select content mode

### content_first
Use when the core value is explanation, argument, framework, checklist, method, or reference.

### image_first
Use when the value is primarily photography, visual taste, object design, architecture, product, or mood.

### experience_first
Use when the sequence itself is the product: story, before/after, reveal, visual journey, escalating comparison.

Do not default to content-first simply because LLMs are good at text.

---

## Stage C — Choose an archetype

Retrieve from `ARCHETYPES_AND_SEQUENCE_BLUEPRINTS.md`.

Selection criteria:
- information type;
- intended viewer change;
- asset availability;
- amount of evidence;
- desired emotional tone;
- CTA;
- novelty pressure.

Do not choose based on the easiest existing design template.

---

## Stage D — Generate 3 cover directions

Each direction must use a different hook mechanism.

Example:

```yaml
candidate_1:
  hook_family: contrarian
  title: "Posting is not marketing"
  visual: "single red phrase inside black typographic field"
  risk: "may feel familiar"
candidate_2:
  hook_family: diagnostic
  title: "Why your posts get attention but no bookings"
  visual: "funnel with visible leak between attention and action"
  risk: "more explanatory, less punchy"
candidate_3:
  hook_family: visual-metaphor
  title: "You are filling the top of a broken funnel"
  visual: "objects pouring into a cracked funnel"
  risk: "metaphor may take longer to decode"
```

Score and select.

---

## Stage E — Design slide 2 as validation

Slide 2 must answer at least one of:
- why should I believe the cover?
- why should I care?
- what exactly are we talking about?
- what is the map of what follows?
- what happened next?

Do not use slide 2 as filler.

---

## Stage F — Allocate idea units

Before writing, decompose the idea into atomic units.

Each unit should be one of:
- claim;
- cause;
- consequence;
- example;
- proof;
- instruction;
- contrast;
- definition;
- transition;
- payoff;
- CTA.

Then group related units into slides.

A slide may contain several micro-units, but one must dominate.

---

## Stage G — Build the sequence curve

Specify the sequence’s movement.

Example educational curve:

```text
STOP -> VALIDATE -> PROBLEM -> MECHANISM -> FRAMEWORK -> EXAMPLE -> APPLICATION -> RESIDUE -> CTA
```

Example story curve:

```text
INTRIGUE -> CONTEXT -> DISRUPTION -> COMPLICATION -> TURN -> RESULT -> MEANING -> AUDIENCE BRIDGE
```

Example visual portfolio curve:

```text
HERO WIDE -> DETAIL -> HUMAN -> ENVIRONMENT -> TEXTURE -> PEAK IMAGE -> QUIET CLOSE
```

The sequence must change state at least every 1–3 slides.

---

# 4. Copy generation constraints

## Per slide

The copy writer must produce:
- primary line;
- optional support line;
- optional labels/callouts;
- optional source/proof note;
- optional continuation cue.

Avoid automatic paragraph writing.

### Copy density categories

**Low**
- one sentence / statement / title;
- 3–20 words typical.

**Medium**
- headline + short explanation;
- one compact list or 2–4 sentences.

**High**
- reference/checklist/framework;
- only when saving/referencing justifies the density.

The generator should vary density according to role.

---

# 5. Visual planning constraints

For every slide define:

```yaml
visual:
  mode: type | photo | diagram | screenshot | illustration | mixed
  role: hero | evidence | demonstration | context | mood | symbol | connector
  composition: stack | split | band | overlap | corner | low_line | frame | punch | grid | editorial | full_bleed | custom
  focal_point: "..."
  supporting_elements: []
  background: "..."
  energy: calm | neutral | intense
  scale: macro | medium | micro
```

No “add some icons for visual interest” as an acceptable instruction.

Every element must have a function.

---

# 6. Novelty engine: how to create new formats

The AI should not “be creative” by adding random effects. It should create novelty through **structured recombination**.

## 6.1 Primitive libraries

Maintain independent libraries for:
- archetypes;
- sequence primitives;
- hook families;
- cover layouts;
- slide layouts;
- visual evidence types;
- rhythm patterns;
- image roles;
- continuity devices;
- CTA patterns;
- texture/material styles;
- diagram families.

A new carousel is a combination across libraries.

Example:

```text
Archetype: Teardown
+ Sequence: escalation + contrast
+ Cover: visual metaphor
+ Layout system: editorial split + occasional full bleed
+ Evidence: annotated screenshots
+ Rhythm: dense -> sparse -> dense -> image -> synthesis
+ CTA: none
```

This can feel new without inventing nonsense.

---

## 6.2 Constraint mutation

To create alternatives, change **one or two dimensions** while preserving the concept.

Examples:
- same sequence, new visual world;
- same visual identity, different archetype;
- same educational content, story architecture instead of list;
- same hook, image-first rather than text-first execution;
- same examples, comparison matrix rather than individual cards.

Avoid changing everything simultaneously.

---

## 6.3 Hybridization

Combine compatible archetypes.

Examples:
- research explainer + narrative;
- case study + mistakes;
- tutorial + teardown;
- reference library + decision tree;
- portfolio + essay;
- local service + myth-busting;
- photo essay + annotated process.

For every hybrid, define:
- primary archetype;
- secondary archetype;
- what each contributes;
- where the transition happens.

---

## 6.4 Novelty distance

Track similarity to recently generated work.

A simple similarity feature vector:

```yaml
features:
  archetype: "..."
  hook_family: "..."
  cover_layout: "..."
  palette_family: "..."
  type_style: "..."
  dominant_visual_mode: "..."
  sequence_engine: "..."
  density_pattern: "..."
  ending_type: "..."
```

If a candidate matches too many recent features, force variation in the lowest-risk dimensions first:
1. layout;
2. rhythm;
3. evidence form;
4. hook family;
5. archetype.

Do not force topic-inappropriate novelty just to maximize difference.

---

## 6.5 Reference usage rules

When using reference carousels:
- extract mechanism;
- never copy wording;
- never copy a full slide sequence unless specifically recreating a format for analysis;
- never copy exact composition + type + imagery together;
- identify what is essential vs stylistic.

Example:

Bad:
> “Use the exact Grow with Alex orange/cream cover and replace the words.”

Good:
> “Use an editorial high-contrast system with a large display word, a restrained supporting sans, one accent color, and a photo integrated as a semantic object.”

---

# 7. Evidence integrity

If a carousel contains factual claims, the AI must maintain a claim ledger.

```yaml
claims:
  - claim: "..."
    source: "..."
    confidence: verified | provided | inference | unsupported
    allowed_language: "..."
```

Rules:
- unsupported numbers are forbidden;
- invented testimonials/results are forbidden;
- “research shows” requires an actual source;
- visual charts cannot imply data that does not exist;
- screenshots should not be fabricated as proof unless clearly illustrative.

This is particularly important because evidence-heavy design can make weak claims look authoritative.

---

# 8. Structural QC before rendering

The planner must answer:

1. What is the viewer change?
2. Why is this archetype appropriate?
3. What does each slide do?
4. What happens if each slide is removed?
5. What specifically makes the viewer continue?
6. Where is the payoff?
7. Which slide is most saveable/shareable, if any?
8. What is the visual evidence strategy?
9. What stays visually invariant?
10. What intentionally varies?

If any answer is vague, revise before rendering.

---

# 9. Render loop

Recommended loop:

```text
PLAN
  -> COVER CONCEPTS
  -> SEQUENCE PLAN
  -> COPY DRAFT
  -> VISUAL PLAN
  -> STRUCTURAL QC
  -> RENDER LOW-FIDELITY CONTACT SHEET
  -> SEQUENCE QC
  -> RENDER FINAL
  -> THUMBNAIL QC
  -> SLIDE QC
  -> FULL-SEQUENCE QC
  -> EXPORT
```

The contact-sheet review is important because problems often appear only when the entire sequence is visible together.

---

# 10. Low-fidelity contact-sheet test

Before expensive image generation or final design, create rough slide thumbnails.

Check:
- sequence rhythm;
- too many identical slides;
- density spikes;
- accidental color repetition;
- whether the cover visually dominates too much or too little;
- whether the closing slide feels like an ending;
- whether the strongest value is buried too late.

This can save substantial generation cost.

---

# 11. Output package for a generated carousel

Each finished carousel should produce:

```text
/carousel_id/
  brief.json
  plan.json
  copy.md
  visual_plan.json
  claims.json
  qc_report.json
  contact_sheet.jpg
  slides/
    01.png
    02.png
    ...
```

Optional:
- caption.md;
- alt_text.md;
- source_refs.md;
- variants/cover_A.png;
- variants/cover_B.png;
- variants/cover_C.png.

---

# 12. Suggested generation roles

For reliability, separate responsibilities.

### Strategist
Defines viewer change, thesis, archetype, sequence.

### Copy planner
Allocates idea units and writes slide copy.

### Visual director
Chooses visual system, assets, layouts, rhythm.

### Renderer
Executes designs/images.

### Critic
Runs QC independently against the spec.

### Fact checker / claim gate
Only required for factual/evidence-heavy content.

These roles can be deterministic pipeline stages; they do not need to be autonomous agents.

---

# 13. Core invariants for the whole system

1. Never start with slide rendering before sequence planning.
2. Never assume text-first is the default.
3. Every slide has one dominant job.
4. Cover and slide 2 are separate optimization problems.
5. Sequence must progress, not merely accumulate.
6. Visuals must have a role.
7. Coherence comes from invariants; variety comes from controlled variables.
8. Evidence must remain honest.
9. Novelty comes from recombination, hybridization, and constraint mutation—not random styling.
10. QC must inspect both individual slides and the complete sequence.
