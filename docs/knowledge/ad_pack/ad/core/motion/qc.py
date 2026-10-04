"""Pre-render QC — deterministic numeric gate over a compiled VideoSpec.

Implements the ``motion_qc`` hard rejections + automated checks that are
measurable before any aesthetic judgement (grammar: ``hard_rejections``,
``automated_checks``): text bounds inside the safe area, minimum font size,
contrast, overlap/density bounds, screen-time per text element, design-system
consistency, and catalogue validity.

Taste stays a human decision on the preview — this gate only stops objectively
broken layouts from ever reaching the renderer or a person.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from kleos.core.motion.schemas import (
    EASING_FAMILIES,
    RESERVED_EASING,
    SCENE_ROLES,
    VideoSpec,
    spec_sha256,
)
from kleos.core.motion.typography import (
    block_height,
    contrast_ratio,
    hex_to_rgb,
    reading_time_seconds,
    wrap_lines,
)

MIN_FONT_SIZE = 40.0
SCENE_MIN_SECONDS = 1.5
SCENE_MAX_SECONDS = 5.0
TOTAL_MIN_SECONDS = 10.0
TOTAL_MAX_SECONDS = 45.0
SCENE_MIN_COUNT = 4
SCENE_MAX_COUNT = 7
CONTRAST_LARGE = 3.0


class QCCheck(BaseModel):
    code: str = Field(min_length=1)
    passed: bool
    note: str | None = None


class QCReport(BaseModel):
    spec_sha256: str | None = None
    checks: list[QCCheck]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    def blocking(self) -> list[QCCheck]:
        return [c for c in self.checks if not c.passed]


def _safe_rect(spec: VideoSpec) -> tuple[float, float, float, float]:
    margin = spec.canvas.margin
    left = spec.render.width * margin
    top = spec.render.height * margin
    right = spec.render.width * (1 - margin)
    bottom = spec.render.height * (1 - margin)
    return left, top, right, bottom


def _text_lines(obj, spec: VideoSpec) -> list[str]:
    if not obj.text:
        return []
    width = obj.w or (spec.render.width * (1 - 2 * spec.canvas.margin))
    font = obj.font_size or MIN_FONT_SIZE
    return wrap_lines(obj.text, font_size=font, width=width)


def _visible_start(obj, scene) -> float:
    starts = [e.t_start for e in scene.events if e.object_id == obj.id]
    return min(starts) if starts else 0.0


def _scene_text_objects(scene):
    return [o for o in scene.objects if o.kind.value == "text"]


def run_qc(spec: VideoSpec) -> QCReport:
    """Run the numeric pre-render gate over a compiled spec."""
    checks: list[QCCheck] = []
    left, top, right, bottom = _safe_rect(spec)
    total = sum(s.duration_seconds for s in spec.scenes)

    def add(code: str, passed: bool, note: str | None = None) -> None:
        checks.append(QCCheck(code=code, passed=passed, note=note))

    # -- band / counts ------------------------------------------------------
    add("duration_band", TOTAL_MIN_SECONDS <= total <= TOTAL_MAX_SECONDS,
        f"total {total:.1f}s (want {TOTAL_MIN_SECONDS:.0f}-{TOTAL_MAX_SECONDS:.0f}s)")
    add("scene_count", SCENE_MIN_COUNT <= len(spec.scenes) <= SCENE_MAX_COUNT,
        f"{len(spec.scenes)} scenes")
    add("role_chain", len(spec.scenes) >= 2 and spec.scenes[0].role.value == "HOOK" and spec.scenes[-1].role.value in ("PAYOFF", "CTA"))

    easing_values = [e.easing for s in spec.scenes for e in s.events if e.easing]
    bridge_types = {s.bridge.type for s in spec.scenes if s.bridge}
    typefaces = {o.font_family for s in spec.scenes for o in s.objects if o.font_family}
    add("design_system", (not bridge_types or bridge_types == {"hard_cut"}) and len(typefaces) <= 1)

    palette = spec.canvas.palette
    add("catalogue_ids", all(r in SCENE_ROLES for r in {s.role.value for s in spec.scenes}))
    add("palette_known", all(_valid_hex(c) for c in palette))

    for scene in spec.scenes:
        sid = scene.id
        scene_seconds = scene.duration_seconds
        add(f"{sid}:scene_seconds", SCENE_MIN_SECONDS <= scene_seconds <= SCENE_MAX_SECONDS,
            f"{scene_seconds:.1f}s")
        text_objs = _scene_text_objects(scene)
        if not text_objs:
            add(f"{sid}:text_present", False, "scene has no text")
            continue

        # attention target: exactly one focal object with motion.
        targets = {o.id for o in text_objs if _visible_start(o, scene) > 0 or any(e.object_id == o.id for e in scene.events)}
        focal = scene.attention_target
        add(f"{sid}:attention", focal in {o.id for o in scene.objects} and focal in targets,
            f"focal={focal}")

        max_events = max(len([e for e in scene.events if e.object_id == o.id]) for o in text_objs)
        add(f"{sid}:object_budget", len(scene.objects) <= 7 and max_events <= 2,
            f"{len(scene.objects)} objects, max {max_events} events/object")

        # -- readability / font / contrast / safe zone ----------------------
        for obj in text_objs:
            oid = obj.id
            font = obj.font_size or 0.0
            add(f"{sid}:{oid}:font", font >= MIN_FONT_SIZE, f"font {font:.0f}px")
            lines = _text_lines(obj, spec)
            height = block_height(lines, font_size=font)
            width = max((len(l) * 0.52 * font for l in lines), default=0.0)
            cx = obj.x if obj.x is not None else spec.render.width / 2
            cy = obj.y if obj.y is not None else spec.render.height / 2
            in_safe = (cx - width / 2 >= left - 0.5) and (cx + width / 2 <= right + 0.5) and (cy - height / 2 >= top - 0.5) and (cy + height / 2 <= bottom + 0.5)
            add(f"{sid}:{oid}:safe", in_safe, f"box {width:.0f}x{height:.0f} @({cx:.0f},{cy:.0f})")

            if obj.color and _valid_hex(obj.color):
                ratio = contrast_ratio(obj.color, spec.canvas.background)
                add(f"{sid}:{oid}:contrast", ratio >= CONTRAST_LARGE, f"contrast {ratio:.1f}")

            show = reading_time_seconds(obj.text or "")
            visible = scene_seconds - _visible_start(obj, scene)
            add(f"{sid}:{oid}:readable", visible >= show - 1e-6, f"visible {visible:.1f}s vs read {show:.1f}s")

        # settle: no text object's last event ends on the final frame.
        for obj in text_objs:
            ends = [e.t_end for e in scene.events if e.object_id == obj.id]
            if ends:
                add(f"{sid}:{obj.id}:settle", max(ends) <= scene_seconds - 0.05)

    # motion consistent with canvas family (or a reserved easing function).
    allowed_easing = EASING_FAMILIES | RESERVED_EASING
    add("easing_consistent", all(v in allowed_easing for v in easing_values))

    return QCReport(spec_sha256=spec_sha256(spec), checks=checks)


def _valid_hex(color: str) -> bool:
    if not isinstance(color, str) or not color.startswith("#"):
        return False
    try:
        hex_to_rgb(color)
        return True
    except ValueError:
        return False
