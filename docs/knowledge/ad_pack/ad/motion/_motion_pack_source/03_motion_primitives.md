# 03 — Motion Primitives

The AI should compose videos from reusable primitives rather than invent raw keyframes scene by scene.

---

# A. Transform primitives

- `translate_linear`
- `translate_eased`
- `translate_arc`
- `scale_focus`
- `scale_pop`
- `scale_breathe`
- `rotate_snap`
- `rotate_continuous`
- `orbit_anchor`
- `depth_push`
- `depth_pull`
- `parallax_shift`
- `camera_pan`
- `camera_zoom`
- `camera_orbit_2_5d`

---

# B. Group choreography primitives

- `fan_out`
- `fan_in`
- `stack`
- `unstack`
- `grid_form`
- `grid_break`
- `rail_form`
- `rail_scroll`
- `radial_form`
- `cluster_attract`
- `cluster_repulse`
- `shuffle`
- `cascade`
- `stagger_enter`
- `stagger_exit`
- `wave_sequence`

Each group primitive should accept:
- item count
- anchor point
- spacing
- delay function
- easing family
- depth behavior
- randomization bounds

---

# C. Reveal primitives

- `mask_wipe`
- `mask_radial`
- `mask_shape`
- `clip_expand`
- `crop_reveal`
- `line_draw`
- `type_on`
- `word_build`
- `character_cascade`
- `blur_to_focus`
- `opacity_fade`
- `scale_from_anchor`

---

# D. Transition primitives

## Object-preserving
Best quality because continuity is maintained.
- `object_match_move`
- `object_match_scale`
- `object_match_rotate`
- `crop_to_scene`
- `card_to_fullscreen`
- `line_to_next_scene`
- `color_field_bridge`

## Scene replacement
- `wipe`
- `push`
- `slide`
- `cut_on_motion`
- `flash_cut`
- `hard_cut`

Use object-preserving transitions whenever possible.

---

# E. Typography primitives

- keyword isolate
- scale hierarchy
- line wrap reveal
- baseline shift
- tracking expansion
- tracking collapse
- word replacement
- strike-through
- highlight block
- underline draw
- masked text fill
- text-on-path
- rotating label
- vertical stack
- kinetic counter

Typography must follow hierarchy; no more than one dominant text event at a time unless intentionally building density.

---

# F. Diagram primitives

- node appear
- node connect
- edge draw
- edge pulse
- branch expand
- branch collapse
- path trace
- state highlight
- state dim
- compare columns
- progress staircase
- funnel compress
- orbit relation
- before/after swap
- timeline advance

---

# G. UI primitives

- browser/device frame
- cursor travel
- click pulse
- selection highlight
- tooltip callout
- zoom-to-control
- scroll window
- card inspect
- panel expand
- state toggle
- result reveal

---

# H. Collage primitives

- paper slide
- tape attach
- sticker pop
- photo drop
- image tilt
- shadow settle
- rip-mask reveal
- photocopy jitter
- grain flicker
- pinboard accumulation

Randomization must stay bounded. The same collage piece should not rotate wildly unless the style explicitly calls for it.

---

# I. Abstract primitives

- concentric expand
- radial repeat
- blob morph
- vector field drift
- particle attract
- particle repel
- ribbon curl
- mesh deform
- torus/orbit motion
- pattern tile
- mirrored symmetry
- recursive frame

---

# J. Timing primitives

- `hit` — 2–6 frame emphasis
- `settle` — 8–18 frames after motion
- `hold` — readability pause
- `stagger` — sequential group delay
- `anticipation` — small movement opposite main direction
- `overshoot` — controlled beyond-target move
- `snap` — short, high-contrast motion
- `drift` — slow background motion

---

# K. Easing vocabulary

Do not choose arbitrary easings per element.
Use style-level easing families:

## Crisp editorial
- fast-out, slow-in
- minimal overshoot

## Playful
- spring / elastic with strict bounds

## Premium
- longer ease-in-out
- lower acceleration contrast

## Tech
- fast snap + short settle

A format spec should select one primary easing family and at most one accent family.
