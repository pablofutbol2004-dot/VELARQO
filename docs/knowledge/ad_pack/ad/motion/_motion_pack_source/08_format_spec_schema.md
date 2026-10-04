# 08 — Format Spec Schema

A format should be stored as structured data rather than only prose.

```yaml
id: F01
name: Kinetic Card Constellation
version: 1.0

intent:
  best_for:
    - collection showcase
    - visual hook
  unsuitable_for:
    - long dense explanation

narrative:
  allowed_roles: [HOOK, ORIENT, BUILD, REVEAL, PAYOFF]
  default_sequence: [HOOK, BUILD, BUILD, REVEAL, PAYOFF]

layout:
  topology: dynamic_group
  anchors: [center, horizontal_rail]
  margin_system: 0.06
  max_primary_objects: 1
  max_secondary_objects: 14

motion:
  primary_family: crisp_editorial
  primitives:
    - fan_out
    - grid_form
    - rail_form
    - object_match_move
  max_transition_families: 2

visual_style:
  background: light
  type_system: modern_sans
  palette_rules:
    max_primary_colors: 4

signature_mechanic:
  description: cards repeatedly reorganize while maintaining identity

assets:
  required:
    - image_cards
  optional:
    - labels

rhythm:
  scene_duration_range: [1.0, 3.0]
  density_curve: [medium, high, low, high, clean]

mutation_axes:
  safe:
    - topology
    - card_count
    - palette
    - camera_path
  risky:
    - material_language

qc:
  must_preserve:
    - object_identity
    - continuity
    - focal_hierarchy
```

## Format instance

The reusable format stays separate from an instance:

```yaml
format_id: F01
content_topic: "10 workshop funnel leaks"
brand_skin: automotive_dark
cards:
  - missed_calls
  - slow_whatsapp
  - weak_reviews
  - ...
mutation_mode: conservative
```
