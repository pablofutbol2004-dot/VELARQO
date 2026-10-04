"""Deterministic compile engine — semantic plan → numeric VideoSpec.

Grammar split (``motion_architecture``): AI writes semantics, code owns layout,
timing, typography, motion events, safe zones and QC. This module is the "code
owns layout" half: it takes a :class:`SemanticVideoPlan` and lays out every
coordinate, font size, duration and motion event, reproducing the three proven
fixture looks (``f03_kinetic_type``, ``editorial_reviews``, ``tech_cards``) over
arbitrary on-screen text.

Everything here is a pure function of the plan + skin + seed — no ``random``, no
wall-clock, no browser. The same (plan, skin, seed) always compiles to the same
spec, so preview and final are deterministic from the same document.
"""

from __future__ import annotations

from kleos.core.motion.plan import PlanScene, SemanticVideoPlan, StyleSkin
from kleos.core.motion.schemas import (
    CanvasSpec,
    MotionEvent,
    RenderConfig,
    RenderMode,
    SceneSpec,
    SpecObject,
    VideoSpec,
)
from kleos.core.motion.typography import (
    block_height,
    lighten,
    line_px,
    reading_time_seconds,
    wrap_lines,
)

CANVAS_W = 1080
CANVAS_H = 1920
FPS = 30
MARGIN = 0.07
CONTENT_W = CANVAS_W * (1 - 2 * MARGIN)  # ~928px safe text width
CENTER_X = CANVAS_W / 2
GAP = 56.0
MIN_SCENE_SECONDS = 2.0
MIN_FONT = 40.0
BAND_TOP = 560.0
BAND_BOTTOM = 1340.0

INK = 0
ACCENT = 1
MUTED = 2

_PRIMARY_TIER = {
    "HOOK": (78, 800),
    "ORIENT": (80, 800),
    "CLAIM": (96, 900),
    "COMPARE": (96, 900),
    "EXPLAIN": (84, 800),
    "DEMO": (84, 800),
    "PROVE": (112, 900),
    "BUILD": (104, 900),
    "REVEAL": (84, 800),
    "TRANSITION": (66, 600),
    "PAYOFF": (124, 900),
    "CTA": (108, 900),
}

_MAX_HERO_LINES = {
    "HOOK": 2, "ORIENT": 2, "CLAIM": 2, "COMPARE": 2, "EXPLAIN": 3, "DEMO": 3,
    "PROVE": 2, "BUILD": 2, "REVEAL": 3, "TRANSITION": 3, "PAYOFF": 2, "CTA": 2,
}

#: Roles that reveal their hero line word-by-word (word_build).
_TOKEN_ROLES = frozenset({"HOOK", "PROVE"})
#: Roles that in the tech_cards format sit on a highlight card.
_PANEL_ROLES = frozenset({"CLAIM", "ORIENT", "COMPARE"})

_NOTE_FONT = 50.0
_FOOT_FONT = 42.0
_KICKER_FONT = 54.0


def _show(text: str) -> float:
    return reading_time_seconds(text)


def _fit(text: str, base: float, max_lines: int) -> tuple[float, list[str]]:
    font = float(base)
    while font >= MIN_FONT:
        lines = wrap_lines(text, font_size=font, width=CONTENT_W)
        if len(lines) <= max_lines:
            return font, lines
        font -= 4.0
    return MIN_FONT, wrap_lines(text, font_size=MIN_FONT, width=CONTENT_W)


def _color(skin: StyleSkin, slot: int) -> str:
    palette = skin.palette or ["#FFFFFF"]
    return palette[slot % len(palette)]


def _ev(object_id: str, primitive: str, start: dict, end: dict, t0: float, t1: float, easing: str) -> MotionEvent:
    return MotionEvent.model_validate(
        {
            "object_id": object_id,
            "primitive": primitive,
            "from": start,
            "to": end,
            "t_start": round(t0, 3),
            "t_end": round(t1, 3),
            "easing": easing,
        }
    )


def _text(id_: str, text: str, *, font_size: float, weight: float, color: str, y: float) -> SpecObject:
    return SpecObject.model_validate(
        {
            "id": id_,
            "kind": "text",
            "text": text,
            "x": CENTER_X,
            "y": round(y, 1),
            "w": CONTENT_W,
            "font_size": font_size,
            "weight": weight,
            "align": "center",
            "color": color,
        }
    )


def _card(id_: str, *, y: float, w: float, h: float, radius: float, fill: str, stroke: str) -> SpecObject:
    return SpecObject.model_validate(
        {
            "id": id_,
            "kind": "card",
            "x": CENTER_X,
            "y": round(y, 1),
            "w": round(w, 1),
            "h": h,
            "radius": radius,
            "fill": fill,
            "stroke": stroke,
            "stroke_width": 2,
        }
    )


def _line(id_: str, *, y: float, w: float, color: str) -> SpecObject:
    return SpecObject.model_validate(
        {
            "id": id_,
            "kind": "line",
            "x": CENTER_X,
            "y": round(y, 1),
            "w": round(w, 1),
            "thickness": 8,
            "color": color,
        }
    )


class _Scene:
    """Everything the compiler knows about one scene, laid out deterministically."""

    def __init__(self, plan: SemanticVideoPlan, scene: PlanScene) -> None:
        self.plan = plan
        self.scene = scene
        self.role = scene.role
        self.easing = plan.skin.easing_family.value
        self.tech = plan.format_id == "tech_cards"
        self.accent = _color(plan.skin, ACCENT)
        self.muted = _color(plan.skin, MUTED)

        p_base, p_weight = _PRIMARY_TIER[self.role]
        self.primary_font, self.primary_lines = _fit(scene.primary, p_base, _MAX_HERO_LINES[self.role])
        self.primary_weight = p_weight
        self.primary_color = _color(plan.skin, ACCENT if self.role in ("PROVE", "PAYOFF", "CTA") else INK)
        self.primary_h = block_height(self.primary_lines, font_size=self.primary_font)
        self.show_p = _show(scene.primary)

        self.kicker_lines: list[str] | None = None
        self.kicker_font = _KICKER_FONT
        self.note_lines: list[str] | None = None
        self.note_font = _FOOT_FONT if self.role in ("PAYOFF", "CTA") else _NOTE_FONT
        if scene.kicker:
            self.kicker_font, self.kicker_lines = _fit(scene.kicker, _KICKER_FONT, 2)
        if scene.note:
            self.note_font, self.note_lines = _fit(scene.note, self.note_font, 2)

    # -- measured geometry ------------------------------------------------------

    def _kicker_h(self) -> float:
        return block_height(self.kicker_lines or [], font_size=self.kicker_font)

    def _note_h(self) -> float:
        return block_height(self.note_lines or [], font_size=self.note_font)

    def _anchors(self) -> dict[str, float]:
        """Deterministic y-center anchors for the scene's elements."""
        y: dict[str, float] = {}
        if self.scene.kicker:
            y["primary"] = 1000.0
            y["kicker"] = 660.0
        elif self.scene.note:
            y["primary"] = 820.0 if self.role == "PROVE" else 880.0
        else:
            y["primary"] = 940.0
        if self.scene.note:
            primary_bottom = y["primary"] + self.primary_h / 2
            y["note"] = max(1160.0, primary_bottom + GAP + self._note_h() / 2)
        if self.role == "PROVE":
            y["underline"] = y["primary"] + self.primary_h / 2 + 70.0
        return y

    def build(self) -> tuple[list[SpecObject], list[MotionEvent], float]:
        token = self.role in _TOKEN_ROLES
        y = self._anchors()
        objects: list[SpecObject] = []
        events: list[MotionEvent] = []
        easing = self.easing
        pid = f"p_{self.scene.id}"

        # -- duration: reveal + reading + settle -----------------------------
        show_n = _show(self.scene.note) if self.scene.note else 0.0
        if token:
            t_reveal = 0.0
            reveal_end = max(0.9, self.show_p)
        else:
            t_reveal = 0.7 if (self.scene.kicker or (self.tech and self.role in _PANEL_ROLES)) else 0.2
            reveal_end = t_reveal + min(1.0, max(0.6, self.show_p * 0.5))
        self.t_reveal = t_reveal
        self.reveal_end = reveal_end
        duration = max(MIN_SCENE_SECONDS, t_reveal + self.show_p + 0.6)
        if self.scene.kicker and self.kicker_lines:
            duration = max(duration, 1.3)
        if self.scene.note:
            n_start = reveal_end + 0.25
            duration = max(duration, n_start + show_n + 0.25)

        # -- primary object ---------------------------------------------------
        objects.append(_text(pid, self.scene.primary, font_size=self.primary_font, weight=self.primary_weight, color=self.primary_color, y=y["primary"]))

        # tech highlight card behind a panel-role statement.
        if self.tech and self.role in _PANEL_ROLES and not token:
            panel_h = max(150.0, self.primary_h + 110)
            objects.insert(0, _card(f"cd_{self.scene.id}", y=y["primary"], w=CONTENT_W, h=panel_h, radius=30, fill=lighten(self.plan.skin.background, 0.05), stroke=self.accent))

        # kicker above the primary.
        if self.scene.kicker and self.kicker_lines:
            kid = f"k_{self.scene.id}"
            tech_pill = self.tech and self.role == "BUILD"
            if tech_pill:
                text_w = max(line_px(l, font_size=self.kicker_font) for l in self.kicker_lines)
                pill_w = min(CONTENT_W, text_w + 70)
                pill_h = max(110.0, self._kicker_h() + 60)
                pill_y = min(y["primary"] - self.primary_h / 2 - 40 - pill_h / 2, 760.0)
                y["kicker"] = pill_y
                objects.append(_card(f"pl_{self.scene.id}", y=pill_y, w=pill_w, h=pill_h, radius=pill_h / 2, fill=lighten(self.plan.skin.background, 0.05), stroke=self._accent2()))
                objects.append(_text(kid, self.scene.kicker, font_size=self.kicker_font, weight=700, color=_color(self.plan.skin, INK), y=pill_y))
                events.append(_ev(f"pl_{self.scene.id}", "scale_pop", {"opacity": 0, "scale": 0.85}, {"opacity": 1, "scale": 1}, 0.15, 0.7, easing))
                events.append(_ev(kid, "opacity_fade", {"opacity": 0}, {"opacity": 1}, 0.35, 0.9, easing))
            else:
                objects.append(_text(kid, self.scene.kicker, font_size=self.kicker_font, weight=500, color=self.muted, y=y["kicker"]))
                events.append(_ev(kid, "translate_eased", {"opacity": 0, "y": y["kicker"] + 54}, {"opacity": 1, "y": y["kicker"]}, 0.0, 0.6, easing))

        # note / foot under the primary.
        if self.scene.note and self.note_lines:
            nid = f"n_{self.scene.id}"
            objects.append(_text(nid, self.scene.note, font_size=self.note_font, weight=500, color=self.muted, y=y["note"]))
            n_start = min(duration - show_n - 0.25, max(0.6, reveal_end + 0.2))
            events.append(_ev(nid, "opacity_fade", {"opacity": 0}, {"opacity": 0.92}, n_start, min(duration - 0.05, n_start + 0.6), easing))

        # -- primary motion -----------------------------------------------------
        if token:
            events.append(_ev(pid, "word_build", {"opacity": 0, "clip": 0, "scale": 0.97}, {"opacity": 1, "clip": 1, "scale": 1}, 0.0, min(duration - 0.2, reveal_end), easing))
            if self.role == "PROVE" and self.scene.note:
                underline_w = min(CONTENT_W * 0.72, max(420.0, len(self.scene.primary) * self.primary_font * 0.5))
                objects.append(_line(f"ln_{self.scene.id}", y=y["underline"], w=underline_w, color=self.accent))
                events.append(_ev(f"ln_{self.scene.id}", "underline_draw", {"opacity": 1, "clip": 0}, {"opacity": 1, "clip": 1}, self.show_p + 0.12, min(duration - 0.05, self.show_p + 0.82), easing))
        else:
            events.append(_ev(pid, "scale_pop", {"opacity": 0, "scale": 0.9}, {"opacity": 1, "scale": 1}, t_reveal, min(duration - 0.15, reveal_end), easing))
            if self.role in ("CLAIM", "BUILD") and len(self.primary_lines) == 1 and duration - reveal_end >= 0.8:
                events.append(_ev(pid, "tracking_expansion", {"tracking": 0}, {"tracking": 6}, duration - 0.65, duration - 0.15, easing))

        return objects, events, duration

    def _accent2(self) -> str:
        palette = self.plan.skin.palette
        return palette[3] if len(palette) > 3 else self.accent


def compile_spec(
    plan: SemanticVideoPlan,
    *,
    mode: RenderMode | str = RenderMode.PREVIEW,
    seed: int | None = None,
) -> VideoSpec:
    """Compile a semantic plan into the numeric VideoSpec the renderer runs."""
    scenes: list[SceneSpec] = []
    for scene in plan.scenes:
        builder = _Scene(plan, scene)
        objects, events, duration = builder.build()
        text_ids = [o.id for o in objects if o.kind.value == "text"]
        scenes.append(
            SceneSpec.model_validate(
                {
                    "id": scene.id,
                    "role": scene.role,
                    "duration_seconds": round(duration, 3),
                    "attention_target": text_ids[0] if text_ids else objects[0].id,
                    "objects": [o.model_dump(mode="json") for o in objects],
                    "events": [e.model_dump(mode="json", by_alias=True) for e in events],
                    "bridge": {"type": "hard_cut"},
                }
            )
        )

    skin = plan.skin
    render = RenderConfig(
        width=CANVAS_W,
        height=CANVAS_H,
        fps=FPS,
        seed=seed if seed is not None else plan.seed,
        mode=RenderMode(mode),
    )
    canvas = CanvasSpec(
        background=skin.background,
        font_family=skin.font_family,
        easing_family=skin.easing_family,
        palette=skin.palette,
        margin=MARGIN,
        radius=skin.radius,
        stroke=skin.stroke,
        grain=skin.grain,
        vignette=skin.vignette,
    )
    return VideoSpec(
        schema_version="1",
        render=render,
        format_id=plan.format_id,
        mutation_mode=plan.mutation_mode,
        canvas=canvas,
        scenes=scenes,
        audio_timeline=[],
    )
