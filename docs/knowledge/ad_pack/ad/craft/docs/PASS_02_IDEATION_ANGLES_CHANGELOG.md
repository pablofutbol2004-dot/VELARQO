# PASS_02_IDEATION_ANGLES_CHANGELOG.md

## Added

- Added `kleos/craft/ideation_angles/essentials.yaml` with 39 rules across 6 categories.
- Added `IDEATION_ANGLES_REFERENCE.md`.
- Added source-level QA and cross-pack duplicate QA.

## Migrated / narrowed

- **`packaging`:** Moved general reference remixing and angle-refresh rules to `ideation_angles`; narrowed `validated_frames` to packaging execution.
- **`content_quality`:** Moved the general originality mechanism into `ideation_angles`; retained a narrower plagiarism/integrity rule.
- **`hooks`:** Moved the general novelty/angle-construction principle to `ideation_angles`; hook-specific familiarity/novelty execution remains.
- **`value_communication`:** Narrowed the generic “make an existing answer novel” rule to explanation/application; angle selection now lives in `ideation_angles`.

## Scope decisions

- `podcast/clip` remains removed from scope.
- Platform-specific trend and algorithm discovery is deliberately excluded and reserved for `channel_ops`.
- Format-specific ideation constraints stay downstream in their format packs.

## Next pass

- `offer_framing`
