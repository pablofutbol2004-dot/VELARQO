# Craft pack — short_form_video

General, engine-level craft knowledge for producing short-form vertical video.
Not business-specific: any pack that runs this format draws on it as applicable.

Two committed artifacts (see `kleos/craft/__init__.py`):

- `SHORT_FORM_VIDEO_CRAFT.md` — the complete reference map (readable, full
  coverage, source-tagged; derived from the operator's two short-form archives,
  distilled by ChatGPT on 2026-09-07).
- `essentials.yaml` — the machine-loaded brief: typed rules per category that
  `kleos.craft.craft_brief("short_form_video", ...)` turns into prompt context
  for the video-script slice (`kleos/core/production/video_script.py`).

Notes:

- Rules are paraphrased guidance, not verbatim passages or embeddable media;
  use them as craft direction, never to reproduce another creator's content.
- Date-sensitive/platform-specific claims are flagged inside the map as things
  to re-check; treat specs as guidance, not gospel.
- Add/refine rules by editing `essentials.yaml` (and the map to match), keeping
  the schema_version bump rule: bump when the shape changes incompatibly.
