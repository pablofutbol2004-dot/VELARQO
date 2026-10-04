"""Canonical VideoSpec schema — the KLEOS↔ZEUS video contract.

This module is the canonical, typed mirror of the renderer-side zod schema in
``services/media_render/src/spec_schema.ts``. Both describe the same numeric
``VideoSpec`` JSON document:

- The **shared catalogues** (``PRIMITIVE_CATALOGUE``, ``SCENE_ROLES``,
  ``EASING_FAMILIES``, ...) are frozensets here and arrays in zod; a conformance
  test asserts they never drift.
- The **pydantic models** validate and serialize the exact JSON the renderer
  consumes. Unknown motion primitive ids fail loudly here (not a silent no-op)
  so planner and renderer cannot drift.

The renderer never decides content: it interpolates the numeric state deltas a
spec declares. This file is deliberately free of layout/planning logic.
"""

from __future__ import annotations

import hashlib
import json
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = "1"

# -- Shared catalogues (mirrors services/media_render/src/spec_schema.ts) ------
# Names come from the motion_primitives knowledge pack. Keep identical to the
# zod PRIMITIVE_CATALOGUE; the conformance test enforces it.

PRIMITIVE_CATALOGUE = frozenset(
    {
        # transforms
        "translate_linear", "translate_eased", "translate_arc", "scale_focus",
        "scale_pop", "scale_breathe", "rotate_snap", "rotate_continuous",
        "orbit_anchor", "depth_push", "depth_pull", "parallax_shift", "camera_pan",
        "camera_zoom", "camera_orbit_2_5d",
        # group choreography
        "fan_out", "fan_in", "stack", "unstack", "grid_form", "grid_break",
        "rail_form", "rail_scroll", "radial_form", "cluster_attract",
        "cluster_repulse", "shuffle", "cascade", "stagger_enter", "stagger_exit",
        "wave_sequence",
        # reveals
        "mask_wipe", "mask_radial", "mask_shape", "clip_expand", "crop_reveal",
        "line_draw", "type_on", "word_build", "character_cascade", "blur_to_focus",
        "opacity_fade", "scale_from_anchor",
        # transitions
        "object_match_move", "object_match_scale", "object_match_rotate",
        "crop_to_scene", "card_to_fullscreen", "line_to_next_scene",
        "color_field_bridge", "wipe", "push", "slide", "cut_on_motion", "flash_cut",
        "hard_cut",
        # typography
        "keyword_isolate", "tracking_expansion", "tracking_collapse",
        "word_replacement", "strike_through", "highlight_block", "underline_draw",
        "masked_text_fill", "text_on_path", "rotating_label", "vertical_stack",
        "kinetic_counter",
        # diagrams
        "node_appear", "node_connect", "edge_draw", "edge_pulse", "branch_expand",
        "branch_collapse", "path_trace", "state_highlight", "state_dim",
        "compare_columns", "progress_staircase", "funnel_compress", "orbit_relation",
        "before_after_swap", "timeline_advance",
        # ui
        "browser_frame", "device_frame", "cursor_travel", "click_pulse",
        "selection_highlight", "tooltip_callout", "zoom_to_control", "scroll_window",
        "card_inspect", "panel_expand", "state_toggle", "result_reveal",
        # collage
        "paper_slide", "tape_attach", "sticker_pop", "photo_drop", "image_tilt",
        "shadow_settle", "rip_mask_reveal", "photocopy_jitter", "grain_flicker",
        "pinboard_accumulation",
        # abstract
        "concentric_expand", "radial_repeat", "blob_morph", "vector_field_drift",
        "particle_attract", "particle_repel", "ribbon_curl", "mesh_deform",
        "torus_orbit_motion", "pattern_tile", "mirrored_symmetry", "recursive_frame",
    }
)

SCENE_ROLES = frozenset(
    {
        "HOOK", "ORIENT", "CLAIM", "EXPLAIN", "COMPARE", "PROVE", "DEMO", "BUILD",
        "REVEAL", "TRANSITION", "PAYOFF", "CTA",
    }
)

EASING_FAMILIES = frozenset({"crisp_editorial", "playful", "premium", "tech"})

#: Reserved per-event easing functions the renderer also accepts (easing.ts).
RESERVED_EASING = frozenset({"linear", "ease_out_cubic", "ease_in_out_smooth"})

MUTATION_MODES = frozenset({"conservative", "exploratory", "experimental"})
RENDER_MODES = frozenset({"preview", "final"})
OBJECT_KINDS = frozenset({"text", "card", "image", "line", "shape", "chat", "arrow"})

#: Format recipes the deterministic compile engine can produce in v1.
FORMAT_RECIPES = frozenset({"f03_kinetic_type", "editorial_reviews", "tech_cards"})

# A MotionEvent interpolates exactly these numeric keys when present in both
# its ``from`` and ``to`` maps; every other key keeps its default.
ANIMATABLE_KEYS = frozenset({"x", "y", "scale", "rotate", "opacity", "tracking", "clip"})


class SceneRole(StrEnum):
    """One semantic job per scene (values serialized exactly as declared)."""

    HOOK = "HOOK"
    ORIENT = "ORIENT"
    CLAIM = "CLAIM"
    EXPLAIN = "EXPLAIN"
    COMPARE = "COMPARE"
    PROVE = "PROVE"
    DEMO = "DEMO"
    BUILD = "BUILD"
    REVEAL = "REVEAL"
    TRANSITION = "TRANSITION"
    PAYOFF = "PAYOFF"
    CTA = "CTA"


class EasingFamily(StrEnum):
    CRISP_EDITORIAL = "crisp_editorial"
    PLAYFUL = "playful"
    PREMIUM = "premium"
    TECH = "tech"


class MutationMode(StrEnum):
    CONSERVATIVE = "conservative"
    EXPLORATORY = "exploratory"
    EXPERIMENTAL = "experimental"


class RenderMode(StrEnum):
    PREVIEW = "preview"
    FINAL = "final"


class ObjectKind(StrEnum):
    TEXT = "text"
    CARD = "card"
    IMAGE = "image"
    LINE = "line"
    SHAPE = "shape"
    CHAT = "chat"
    ARROW = "arrow"


# -- Spec models --------------------------------------------------------------


class RenderConfig(BaseModel):
    """Output canvas + determinism configuration."""

    width: int = Field(default=1080, gt=0, description="Output MP4 width, px")
    height: int = Field(default=1920, gt=0, description="Output MP4 height, px")
    fps: int = Field(default=30, gt=0)
    seed: int = Field(default=0, description="Determinism seed")
    mode: RenderMode = RenderMode.PREVIEW


class CanvasAccent(BaseModel):
    """One authored background colour field (deterministic, no seed needed)."""

    x: float
    y: float
    radius: float
    color: str = Field(min_length=1)
    opacity: float = Field(ge=0, le=1)


class CanvasSpec(BaseModel):
    """The one design system a whole video shares (palette/type/motion)."""

    background: str = Field(default="#0E0E14", min_length=1)
    font_family: str = Field(default="Inter", min_length=1)
    easing_family: EasingFamily = EasingFamily.CRISP_EDITORIAL
    palette: list[str] = Field(min_length=1, description="≥1 color; KLEOS emits 4 slots")
    margin: float = Field(default=0.07, ge=0, le=0.5)
    radius: float = Field(default=12)
    stroke: float = Field(default=2)
    grain: bool = False
    vignette: bool = False
    accents: list[CanvasAccent] | None = None

    @field_validator("palette")
    @classmethod
    def _palette_colors(cls, value: list[str]) -> list[str]:
        for entry in value:
            if not str(entry).strip():
                raise ValueError("palette colors must be non-empty")
        return value


class ChatMessage(BaseModel):
    """One message bubble in a phone-thread (``chat``) object."""

    model_config = ConfigDict(populate_by_name=True)

    from_: Literal["client", "shop", "system"] = Field(alias="from")
    text: str = Field(min_length=1)
    time: str | None = None


class SpecObject(BaseModel):
    """A typed object inside a scene (renderer uses what it knows, tolerates more)."""

    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1)
    kind: ObjectKind
    x: float | None = Field(default=None, description="Center x, px")
    y: float | None = Field(default=None, description="Center y, px")
    w: float | None = Field(default=None, gt=0, description="Box width, px")
    h: float | None = Field(default=None, gt=0, description="Box height, px")
    text: str | None = None
    font_size: float | None = Field(default=None, gt=0)
    weight: float | None = None
    align: Literal["left", "center", "right"] | None = None
    color: str | None = None
    radius: float | None = Field(default=None, description="Corner radius / circle")
    fill: str | None = Field(default=None, description="Card/box background")
    stroke: str | None = Field(default=None, description="Border color")
    stroke_width: float | None = None
    image: str | None = Field(default=None, description="data: URL or staticFile path")
    thickness: float | None = Field(default=None, description="Line height, px")
    font_family: str | None = None
    case: Literal["upper", "lower", "none"] | None = None
    line_height: float | None = None
    letter_spacing: float | None = None
    anchor_x: Literal["left", "center", "right"] | None = None
    title: str | None = None
    subtitle: str | None = None
    messages: list[ChatMessage] | None = None


class MotionEvent(BaseModel):
    """One numeric state delta for one object (the renderer's unit of motion)."""

    model_config = ConfigDict(populate_by_name=True)

    object_id: str = Field(min_length=1)
    primitive: str = Field(min_length=1)
    from_: dict[str, float] | None = Field(default=None, alias="from")
    to_: dict[str, float] | None = Field(default=None, alias="to")
    t_start: float = Field(default=0.0, ge=0, description="Scene-local seconds")
    t_end: float = Field(ge=0, description="Scene-local seconds")
    easing: str | None = None

    @field_validator("primitive")
    @classmethod
    def _primitive_known(cls, value: str) -> str:
        if value not in PRIMITIVE_CATALOGUE:
            raise ValueError(f"unknown motion primitive {value!r}; see PRIMITIVE_CATALOGUE")
        return value

    @field_validator("easing")
    @classmethod
    def _easing_known(cls, value: str | None) -> str | None:
        if value is not None and value not in EASING_FAMILIES and value not in RESERVED_EASING:
            raise ValueError(f"unknown easing {value!r}")
        return value

    @model_validator(mode="after")
    def _numeric_delta(self) -> MotionEvent:
        if self.t_end <= self.t_start:
            raise ValueError(f"event t_end ({self.t_end}) must be after t_start ({self.t_start})")
        start = self.from_ or {}
        end = self.to_ or {}
        if not start or not end:
            raise ValueError(f"event {self.object_id}:{self.primitive} needs both from and to")
        shared = set(start).intersection(end)
        if not shared:
            raise ValueError(
                f"event {self.object_id}:{self.primitive} must interpolate a shared numeric key; "
                f"from={sorted(start)} to={sorted(end)}"
            )
        for state in (start, end):
            for key in state:
                if key not in ANIMATABLE_KEYS:
                    raise ValueError(f"event key {key!r} is not animatable; {ANIMATABLE_KEYS}")
        return self


class BridgeSpec(BaseModel):
    """A declared transition between scenes (metadata to the current renderer)."""

    type: str = Field(min_length=1)
    object_id: str | None = None


class SceneSpec(BaseModel):
    """One semantic unit of the video: objects + the events that move them."""

    id: str = Field(min_length=1)
    role: SceneRole
    duration_seconds: float = Field(gt=0, description="Defines the timeline")
    attention_target: str | None = None
    objects: list[SpecObject] = Field(min_length=1)
    events: list[MotionEvent] = Field(default_factory=list)
    bridge: BridgeSpec | None = None

    @model_validator(mode="after")
    def _references_resolve(self) -> SceneSpec:
        object_ids = [obj.id for obj in self.objects]
        duplicates = {i for i in object_ids if object_ids.count(i) > 1}
        if duplicates:
            raise ValueError(f"scene {self.id} repeats object ids {sorted(duplicates)}")
        for event in self.events:
            if event.object_id not in object_ids:
                raise ValueError(
                    f"scene {self.id} event references unknown object "
                    f"{event.object_id!r} (have {sorted(object_ids)})"
                )
        if self.attention_target is not None and self.attention_target not in object_ids:
            raise ValueError(f"scene {self.id} attention_target not in objects")
        if self.bridge is not None and self.bridge.object_id is not None and self.bridge.object_id not in object_ids:
            raise ValueError(f"scene {self.id} bridge references unknown object")
        return self


class VideoSpec(BaseModel):
    """The full numeric video document the renderer executes."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1"] = SCHEMA_VERSION
    render: RenderConfig = Field(default_factory=RenderConfig)
    format_id: str = Field(min_length=1)
    mutation_mode: MutationMode = MutationMode.CONSERVATIVE
    canvas: CanvasSpec
    scenes: list[SceneSpec] = Field(min_length=1)
    audio_timeline: list[Any] = Field(default_factory=list)


def parse_spec(data: dict[str, Any]) -> VideoSpec:
    """Validate raw JSON into a canonical :class:`VideoSpec` (fails loudly)."""
    return VideoSpec.model_validate(data)


def dump_spec(spec: VideoSpec) -> dict[str, Any]:
    """Serialize a spec to the exact JSON the renderer consumes.

    Unset optional fields are dropped (``exclude_none``): zod's ``.optional()``
    accepts an absent key but rejects an explicit ``null``, so nulls would make a
    valid spec fail the renderer's validator.
    """
    return spec.model_dump(mode="json", by_alias=True, exclude_none=True)


def spec_sha256(spec: VideoSpec | dict[str, Any]) -> str:
    """Stable content hash of a spec (canonical JSON, sorted keys)."""
    if isinstance(spec, VideoSpec):
        data = dump_spec(spec)
    else:
        data = parse_spec(spec)
        data = dump_spec(data)
    canonical = json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
