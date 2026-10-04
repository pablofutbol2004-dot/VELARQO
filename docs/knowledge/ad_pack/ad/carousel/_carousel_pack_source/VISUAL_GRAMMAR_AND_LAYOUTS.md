# Visual Grammar and Layouts

## 1. Visual grammar = invariants + controlled variables

A carousel feels designed when it has a coherent visual language and intentional variation.

Before designing individual slides, define:

### Invariants
Elements that remain stable:
- type families;
- accent color(s);
- margin system;
- texture/background treatment;
- corner radius/border language;
- icon/diagram style;
- image treatment;
- slide numbering/navigation;
- micro-header/footer style.

### Variables
Elements allowed to change:
- headline scale;
- image position;
- text/image ratio;
- density;
- background tone;
- crop;
- diagram type;
- number of columns;
- full-bleed vs framed image.

The AI should never vary everything at once.

---

## 2. Hierarchy: one thing wins

**CORE**

Every slide needs a dominant entry point.

Hierarchy is created with:
- size;
- weight;
- position;
- contrast;
- color;
- whitespace;
- isolation;
- framing;
- scale of imagery.

The typography-mistakes carousel explicitly demonstrates weak vs strong hierarchy; the broader corpus reinforces it.

Useful hierarchy levels:
- Level 1: dominant idea / headline;
- Level 2: explanation / label;
- Level 3: metadata / footer / annotation.

Avoid 4–6 equally loud typographic levels unless the content truly requires them.

---

## 3. Typography as both language and shape

The corpus repeatedly uses type as a visual object, especially in editorial and educational carousels.

### Useful roles
- large display headline = focal shape;
- serif italic/display = editorial/emotional emphasis;
- grotesk/sans = clarity and utility;
- condensed bold = force/impact;
- small mono/microtext = metadata/system feel.

### Strong pairing principle from source material
A useful source-derived heuristic:
- one **loud** font for impact;
- one **quiet** font for clarity.

This is more transferable than saving fixed font pairs.

### Do not encode as universal
“Two fonts maximum” is a useful simplicity constraint, not a law.

---

## 4. Line length and line spacing

The typography reference carousel gives specific heuristics:
- line length around 45–75 characters;
- line height around 120–150%.

Treat these as **source-derived starting ranges**, not rigid rules.

For carousel generation, the more important operational test is:
- can the body copy be read comfortably at mobile size?
- does the text block have a clear rag/shape?
- does line spacing support scanning?

Long paragraphs should be rare unless the carousel deliberately uses an essay aesthetic.

---

## 5. Alignment

The addendum contains “don’t center align your text,” but the corpus itself includes successful centered compositions.

Therefore:

> **Alignment should follow content and reading order, not ideology.**

Use left alignment for:
- paragraphs;
- lists;
- dense explanations;
- sequential reading.

Use centered alignment for:
- short statements;
- covers;
- symmetrical compositions;
- punchlines;
- high-whitespace slides.

The actual failure is usually poor hierarchy or awkward line lengths, not center alignment itself.

---

## 6. Spacing systems

The grid and typography carousels repeatedly reinforce:
- consistent margins;
- consistent internal gaps;
- alignment across related elements;
- baseline/spacing rhythm.

A practical AI rule:

Choose a base spacing unit `u` and construct most gaps from a small scale such as:
- 1u;
- 2u;
- 3u;
- 4u;
- 6u;
- 8u.

Do not randomly invent every gap.

This makes complex slides feel calm even when they contain many elements.

---

## 7. Grid vocabulary extracted from the corpus

The Expert Pitch carousel teaches six grid types. Treat this taxonomy as source-derived design vocabulary.

### Radial grid
Elements organize around a central point.
Useful for:
- hero-centered posters;
- radiating categories;
- strong focal centers.

### Modular grid
Rows + columns create repeatable cells.
Useful for:
- dashboards;
- collections;
- comparisons;
- galleries;
- repeated content units.

### Column grid
Vertical columns organize text and images.
Useful for:
- editorial layouts;
- articles;
- responsive-looking cards;
- multiple content zones.

### Hierarchical grid
Importance determines size and placement rather than equal modules.
Useful for:
- marketing posters;
- dynamic editorial layouts;
- strong visual hierarchy.

### Baseline grid
Text aligns to repeated horizontal rhythm.
Useful for:
- typography-heavy slides;
- editorial consistency.

### Axial grid
Elements organize around a central axis.
Useful for:
- balance;
- strong directional composition;
- poster-like layouts.

The AI does not need to label the grid in output; it should use the grid as a composition strategy.

---

## 8. Golden-ratio material: use cautiously

The corpus includes a Golden Ratio explainer and examples of spiral overlays.

What is useful for generation:
- proportional relationships can create coherent scale systems;
- focal points can be positioned intentionally rather than arbitrarily;
- composition can guide the eye through asymmetry.

What should **not** be treated as established by the corpus:
- that the Golden Ratio is universally more beautiful;
- that it automatically creates psychologically superior design;
- that it must be used for strong composition.

Use it as an optional compositional device, not a quality requirement.

---

## 9. Image roles

Images in the corpus perform distinct jobs. The generator should tag each image with one.

### Hero
The image is the main event.

### Evidence
Shows the thing being claimed.
- screenshot;
- before/after;
- real example;
- chart;
- process photo.

### Demonstration
Shows how a step works.

### Context
Establishes environment, identity, or use case.

### Mood
Creates emotion or brand world.

### Symbol
Represents an abstract concept through a recognizable object or scene.

### Texture
Adds visual richness with minimal semantic burden.

### Connector
An image chosen because it visually bridges adjacent slides by color, shape, subject, or camera scale.

Do not choose images only by “looks cool.”

---

## 10. Image-first sequencing

Visual carousels such as travel, automotive detail, product art direction, and architectural storytelling reveal several useful sequencing controls.

### Scale rhythm
- wide establishing;
- medium subject;
- close detail;
- return to wide.

### Subject rhythm
- object;
- human interaction;
- environment;
- texture;
- object again.

### Color rhythm
Repeat accent colors across separated slides to create cohesion.

### Direction rhythm
Alternate left/right visual weight or preserve directional flow intentionally.

### Energy rhythm
- calm;
- active;
- calm;
- peak;
- resolution.

### Narrative curation
For architectural/brand storytelling:
- place;
- arrival;
- interaction;
- lived moment;
- detail;
- emotional payoff.

---

## 11. Before/after as a visual device

The Eks Designs carousel uses black-and-white vs color to encode past vs present within each slide.

This reveals a general device:

> Use a repeated visual transformation to carry the conceptual transformation.

Other possible mappings:
- blur → sharp;
- grayscale → color;
- cluttered → clean;
- small → large;
- dark → light;
- empty → populated;
- raw → polished.

The transformation should have semantic meaning, not be a random effect.

---

## 12. Repetition systems

Reference carousels benefit from repeated card structures.

Good repetition:
- same label position;
- same headline system;
- same example area;
- same annotation structure;
- controlled color changes.

Bad repetition:
- every slide visually identical despite different content needs.

Use repeated modules when comparison is the goal.
Use freer layouts when emotional pacing or narrative is the goal.

---

## 13. Whitespace

Whitespace functions as:
- hierarchy;
- pacing;
- confidence;
- separation;
- focus;
- visual relief.

The source claim “remove 30%” is not a universal metric, but its underlying point is strong:

> Every element should justify the attention it consumes.

Do not treat whitespace as emptiness that must be filled.

---

## 14. Color systems

The corpus uses several successful strategies:

### One accent + neutrals
Common in educational/editorial work.
Benefits:
- clear emphasis;
- easy consistency;
- strong recognizability.

### Alternating two backgrounds
Used in long text essays.
Benefits:
- rhythm;
- page-turn feeling;
- low-complexity variation.

### Full-image palette
Let photography establish color; typography remains restrained.

### High-contrast brand palette
Black/white + orange/red/yellow used for punchy educational systems.

### Mood palette
Muted earth, cream, dark green, warm brown for reflective/architectural content.

Choose color for function:
- emphasis;
- category coding;
- mood;
- continuity;
- contrast.

Do not use multiple accents merely to make the carousel “dynamic.”

---

## 15. Texture and materiality

Many strong carousels use subtle texture:
- paper grain;
- film grain;
- soft noise;
- print-like backgrounds;
- scanned/editorial artifacts.

This can make digital slides feel less sterile, but it is **style**, not a core rule.

AI failure mode:
- excessive fake grain, glow, paper tears, chromatic aberration, or “editorial” effects used as a substitute for composition.

---

## 16. Diagrams

Useful diagram families observed:
- funnel;
- grid/matrix;
- radial map;
- before/after;
- flowchart;
- staircase/path;
- cycle/flywheel;
- comparison columns;
- annotated image;
- layered stack;
- numbered sequence;
- progress meter.

Diagram rule:

> A diagram should make a relationship easier to see than text alone.

Do not create a diagram when the content is simply a list.

---

## 17. Screenshots and interface frames

The corpus frequently places screenshots inside:
- phone mockups;
- rounded cards;
- browser-like frames;
- highlighted annotations.

Use screenshots for:
- proof;
- process;
- product/tool context;
- before/after comparison.

Avoid screenshot decoration that makes the actual relevant area too small to read.

---

## 18. Typography + imagery integration

Three broad modes:

### Overlay
Text over image.
Best when negative space and contrast exist.

### Separation
Text and image occupy distinct zones.
Best for clarity and busy imagery.

### Interlock
Text intentionally overlaps or wraps around the subject.
Best for expressive editorial covers.

The AI should infer which mode fits from image complexity and desired tone.

---

## 19. Visual continuity devices

Use one or more across slides:
- same horizon line;
- repeated shape;
- repeated object;
- color carryover;
- continuing line/arrow;
- recurring frame;
- consistent number badge;
- recurring typographic phrase;
- image crop progression;
- same model/person in changing contexts.

Continuity should be perceptible but not necessarily literal.

---

## 20. Visual rhythm planner

Before rendering, assign each slide:

- **density:** low / medium / high;
- **dominant mode:** type / image / diagram / screenshot / mixed;
- **energy:** calm / neutral / intense;
- **scale:** macro / medium / micro;
- **background:** light / dark / image / accent;
- **layout family:** stack / split / frame / editorial / grid / full-bleed / etc.

Then inspect the sequence.

Avoid patterns like:
- 10 high-density text slides;
- 10 identical centered statements;
- 10 full-bleed photos at the same crop scale;
- random alternation with no visual logic.

---

## 21. Visual system selection by content type

### Dense educational/reference
Use:
- grid;
- repeated card structure;
- clear labels;
- restrained palette;
- high hierarchy.

### Thought leadership essay
Use:
- strong type;
- large whitespace;
- controlled color alternation;
- occasional diagram/example.

### High-energy growth/content education
Use:
- bold display type;
- strong accent;
- image worlds;
- varied layouts inside fixed brand rules.

### Local automotive service
Use:
- real car/process photography;
- strong subject crops;
- service-relevant overlays;
- diagnostic or lifestyle copy;
- local/seasonal specificity.

### Portfolio / art direction
Use:
- minimal text;
- strong curation;
- scale rhythm;
- visual callbacks;
- coherent color world.
