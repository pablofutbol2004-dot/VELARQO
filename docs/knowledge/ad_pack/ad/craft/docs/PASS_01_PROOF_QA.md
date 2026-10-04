# Pass 01 — Proof — QA report

- YAML packs parsed successfully: **13/13**.
- Total general-craft rules after migration: **206**.
- Exact normalized cross-pack duplicate rules: **0**.
- High lexical-similarity cross-pack duplicate candidates (SequenceMatcher ≥ 0.82): **0**.
- TF-IDF semantic-ish cross-pack duplicate candidates (cosine ≥ 0.48): **0**.
- New `C12K` provenance references in `proof`: **52**; source file resolution: **52/52**; cited timestamp resolution: **52/52**.
- `podcast/clip`: **no pack exists** and it is absent from the active roadmap; the term appears only in explicit removal notes.

## Rule counts

| Pack | Rules |
|---|---:|
| `attention` | 12 |
| `content_measurement` | 20 |
| `content_quality` | 16 |
| `copywriting` | 15 |
| `cta_conversion` | 11 |
| `editing` | 18 |
| `hooks` | 17 |
| `packaging` | 12 |
| `proof` | 28 |
| `spoken_writing` | 12 |
| `storytelling` | 16 |
| `value_communication` | 15 |
| `visual_communication` | 14 |

## QA caveat

- Duplicate scans catch textual/lexical overlap, not every possible conceptual overlap. The proof migration therefore also received a manual boundary review against `value_communication`, `visual_communication`, `cta_conversion`, `hooks`, `content_quality`, `packaging`, and `content_measurement`.
