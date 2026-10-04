# 04 — Scene Grammar

## Core concept

A scene is not just a visual frame. It is a **semantic beat expressed as a state transition**.

---

# 1. Scene roles

Every scene should declare one role:

- `HOOK`
- `ORIENT`
- `CLAIM`
- `EXPLAIN`
- `COMPARE`
- `PROVE`
- `DEMO`
- `BUILD`
- `REVEAL`
- `TRANSITION`
- `PAYOFF`
- `CTA`

This prevents visually impressive but purposeless scenes.

---

# 2. Scene object model

Each scene contains:

```yaml
scene_id: s03
role: EXPLAIN
semantic_goal: show that three inputs combine into one output
attention_target: output_card
objects:
  - id: input_a
    type: card
  - id: input_b
    type: card
  - id: input_c
    type: card
  - id: output_card
    type: card
relations:
  - input_a -> output_card
  - input_b -> output_card
  - input_c -> output_card
initial_state: inputs separated, output hidden
motion_event: inputs converge, edges draw, output expands
final_state: output centered, inputs secondary
exit_bridge: output_card
```

---

# 3. Readability constraints

At any time:

- maximum 1 primary focal object
- maximum 2–4 secondary objects unless intentionally showing scale
- text must remain readable long enough for its complexity
- do not animate every object simultaneously
- foreground motion should dominate background motion

---

# 4. Scene chaining rules

## Good chain
`HOOK -> ORIENT -> EXPLAIN -> PROVE -> PAYOFF`

## Tutorial
`HOOK -> DEMO -> EXPLAIN -> DEMO -> RESULT`

## Brand
`HOOK -> IDENTITY -> DETAIL -> SYSTEM -> PAYOFF`

## Case study
`PROBLEM -> EVIDENCE -> DIAGNOSIS -> INTERVENTION -> RESULT`

---

# 5. Bridge design

Every scene transition should select one bridge:

- shared object
- shared color
- shared line/path
- shared crop
- shared word
- shared camera direction
- deliberate hard cut on audio beat

A video with no transition logic will feel like a slideshow even if each scene is individually beautiful.

---

# 6. Rhythm grammar

Recommended default for 15–40s motion content:

- first visual change: < 1s
- hook state should stabilize quickly enough to read
- major semantic beat: ~1.5–4s depending on complexity
- micro-change inside longer beats every ~0.4–1.2s
- deliberate pauses are allowed when visual density is high

Do not force a cut every second. Continuous transformation often feels more premium.

---

# 7. Density wave

A strong default density pattern:

`medium -> high -> low -> medium -> high -> clean payoff`

Avoid:

`high -> high -> high -> high`

unless producing a deliberately maximalist style.

---

# 8. Asset-role mapping

Each asset should have a semantic role:

- **evidence** — screenshot/photo/data
- **metaphor** — icon/object representing concept
- **anchor** — recurring visual object
- **texture** — non-semantic atmosphere
- **label** — text that clarifies

If an asset has no role, remove it.
