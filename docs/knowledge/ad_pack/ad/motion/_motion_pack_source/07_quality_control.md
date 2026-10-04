# 07 — Quality Control / Anti-Slop Rules

## Hard rejection checks
Reject a render if any of these occur:

- text clipped or outside safe zone
- unreadable text duration
- overlapping semantic objects unintentionally
- inconsistent fonts/palette without explicit reason
- random transition style changes
- obvious low-res assets
- mismatched corner radii/strokes
- movement starts/stops awkwardly
- no clear focal object
- transitions disconnect scene logic
- excessive simultaneous motion
- generic decorative assets with no purpose

---

# Scoring rubric (100)

## 1. Clarity — 25
- focal hierarchy
- readable text
- concept understandable

## 2. Motion quality — 20
- easing
- continuity
- timing
- purposeful animation

## 3. Composition — 15
- spacing
- alignment
- balance
- crop quality

## 4. Design-system consistency — 15
- palette
- typography
- shapes
- texture/material

## 5. Narrative progression — 10
- each beat adds meaning
- payoff resolves setup

## 6. Novelty — 10
- not generic template output
- signature mechanic present

## 7. Asset quality — 5
- sharpness
- coherent style

Production threshold: **>= 82/100** and no hard rejection.

---

# Common AI-slop failure modes

## Random creativity
Symptom: each scene uses a new visual idea.
Fix: enforce one design system and one signature mechanic.

## Everything moves
Symptom: no hierarchy.
Fix: designate attention target; background elements move less.

## Template obviousness
Symptom: same scene skeleton repeated endlessly.
Fix: vary scene topology while preserving format grammar.

## Fake complexity
Symptom: particles, 3D, noise, glow used without reason.
Fix: every effect needs semantic or stylistic justification.

## Dead slideshow
Symptom: static posters with zoom transitions.
Fix: express information as state changes and object continuity.

## Unreadable typography
Symptom: beautiful but too fast.
Fix: estimate reading time from word count and complexity.

---

# Automated QC checks

Possible deterministic tests:
- text bounding boxes within safe area
- minimum font size
- contrast ratio
- overlap detection
- screen-time per text element
- scene density count
- palette deviation
- typeface count
- transition-type count
- motion velocity spikes
- empty-frame detection

Visual-model QC can additionally judge:
- hierarchy
- polish
- awkward crops
- perceived coherence
- novelty
