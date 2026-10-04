"""Semantic video planning — the KLEOS half of the motion pipeline.

The grammar (``motion_architecture``) splits labour deliberately: a language
model *chooses and writes* the semantic layer — the format family, the scene
roles, and which words appear on screen, bounded to what the piece may assert —
while deterministic code owns layout, timing, safe zones and QC. This module is
that semantic layer: a typed :class:`SemanticVideoPlan` a model drafts (or an
operator authors by hand), which ``compile`` then turns into a numeric
``VideoSpec``.

A plan is NOT a spec: it carries no coordinates, durations or easing — those are
the compiler's job. A plan is also NOT copy: every on-screen line stays grounded
in the piece's allowed claims (``packet_context``) and never invents facts.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field, model_validator

from kleos.core.motion.schemas import FORMAT_RECIPES, SCENE_ROLES, EasingFamily

#: Named skins (palette/type/motion systems) the operator can dial between.
DEFAULT_SKINS: dict[str, StyleSkin] = {}
FORMAT_DEFAULT_SKIN: dict[str, str] = {}


def _build_skins() -> None:
    DEFAULT_SKINS["dark_editorial"] = StyleSkin(
        background="#0E0E14",
        palette=["#FFFFFF", "#FF5C39", "#B9BEC9", "#1B1B22"],
        easing_family=EasingFamily.CRISP_EDITORIAL,
    )
    DEFAULT_SKINS["light_premium"] = StyleSkin(
        background="#F6F2EA",
        palette=["#14100C", "#C2410C", "#6B6256", "#FFFFFF"],
        easing_family=EasingFamily.PREMIUM,
        radius=14.0,
    )
    DEFAULT_SKINS["dark_tech"] = StyleSkin(
        background="#07121A",
        palette=["#FFFFFF", "#22D3EE", "#8AA0AE", "#6366F1"],
        easing_family=EasingFamily.TECH,
        radius=16.0,
    )
    FORMAT_DEFAULT_SKIN.update(
        f03_kinetic_type="dark_editorial",
        editorial_reviews="light_premium",
        tech_cards="dark_tech",
    )


def default_skin_for(format_id: str) -> StyleSkin:
    """The proven default skin for a format recipe."""
    if not DEFAULT_SKINS:
        _build_skins()
    name = FORMAT_DEFAULT_SKIN.get(format_id, "dark_editorial")
    return DEFAULT_SKINS[name]


def resolve_skin(skin: StyleSkin | str | None) -> StyleSkin:
    """Accept a skin object, a named skin, or None (dark editorial default)."""
    if isinstance(skin, StyleSkin):
        return skin
    if not DEFAULT_SKINS:
        _build_skins()
    if skin is None:
        return DEFAULT_SKINS["dark_editorial"]
    if skin not in DEFAULT_SKINS:
        raise ValueError(f"unknown skin {skin!r}; have {sorted(DEFAULT_SKINS)}")
    return DEFAULT_SKINS[skin]


class StyleSkin(BaseModel):
    """Art direction as data — one design system a whole video shares."""

    background: str = "#0E0E14"
    palette: list[str] = Field(
        default_factory=lambda: ["#FFFFFF", "#FF5C39", "#B9BEC9", "#1B1B22"]
    )
    easing_family: EasingFamily = EasingFamily.CRISP_EDITORIAL
    font_family: str = "Inter"
    radius: float = 12.0
    stroke: float = 2.0
    grain: bool = False
    vignette: bool = False

    @model_validator(mode="after")
    def _skin_sane(self) -> StyleSkin:
        if len(self.palette) != 4:
            raise ValueError(f"skin palette must have exactly 4 colors, got {len(self.palette)}")
        return self


class PlanScene(BaseModel):
    """One semantic beat: which words appear on screen, and their scene role."""

    id: str = Field(min_length=1)
    role: str = Field(min_length=1, description="One of SCENE_ROLES (HOOK..CTA)")
    primary: str = Field(min_length=1, description="The main on-screen line (short)")
    kicker: str | None = Field(default=None, description="Lead-in / context line above")
    note: str | None = Field(default=None, description="Muted support line below")

    @model_validator(mode="after")
    def _role_known(self) -> PlanScene:
        if self.role not in SCENE_ROLES:
            raise ValueError(f"unknown scene role {self.role!r}; choose from {sorted(SCENE_ROLES)}")
        return self


class SemanticVideoPlan(BaseModel):
    """The semantic layer of one video, before layout/QC decisions."""

    schema_version: str = "1"
    format_id: str = Field(min_length=1)
    business_id: str | None = None
    run_id: str | None = None
    caption: str | None = None
    mutation_mode: str = "conservative"
    skin: StyleSkin = Field(default_factory=StyleSkin)
    seed: int = 0
    scenes: list[PlanScene] = Field(min_length=4, max_length=7)

    @model_validator(mode="after")
    def _shape_sane(self) -> SemanticVideoPlan:
        if self.format_id not in FORMAT_RECIPES:
            raise ValueError(f"unknown format {self.format_id!r}; have {sorted(FORMAT_RECIPES)}")
        ids = [s.id for s in self.scenes]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate scene ids in plan: {sorted(ids)}")
        first, last = self.scenes[0].role, self.scenes[-1].role
        if first != "HOOK":
            raise ValueError(f"a plan must open with a HOOK scene, got {first!r}")
        if last not in ("PAYOFF", "CTA"):
            raise ValueError(f"a plan must close with PAYOFF or CTA, got {last!r}")
        return self


# ---------------------------------------------------------------------------
# Craft-grounded semantic planning (the AI layer, bounded by the piece)
# ---------------------------------------------------------------------------

_MOTION_PACKS = (
    "motion_scene_grammar",
    "motion_principles",
    "motion_formats",
    "motion_qc",
)
_MOTION_CATEGORIES = (
    "design_constraints",
    "composition_principle",
    "F03_kinetic_type_argument",
    "scene_roles",
    "readability",
    "chaining",
    "density_wave",
    "hard_rejections",
    "slop_failure_modes",
)


def motion_craft_brief(*, max_chars: int = 3600) -> str:
    """Deterministic craft guidance for planning a video, composed from the packs."""
    from kleos.craft import craft_compose

    return craft_compose(_MOTION_PACKS, categories=_MOTION_CATEGORIES, max_chars=max_chars)


def plan_from_data(
    data: dict[str, Any],
    *,
    skin: StyleSkin,
    seed: int = 0,
    business_id: str | None = None,
    run_id: str | None = None,
    caption: str | None = None,
) -> SemanticVideoPlan:
    """Validate a model/operator-authored plan document into a typed plan."""
    format_id = str(data.get("format_id") or "").strip()
    scenes_raw = data.get("scenes")
    if not format_id:
        raise ValueError("a video plan needs a format_id")
    if not isinstance(scenes_raw, list) or not scenes_raw:
        raise ValueError("a video plan needs a non-empty scenes list")
    scenes = []
    for i, row in enumerate(scenes_raw):
        if not isinstance(row, dict):
            raise TypeError(f"scene {i} is not an object")
        scenes.append(PlanScene.model_validate(row))
    return SemanticVideoPlan(
        schema_version="1",
        format_id=format_id,
        business_id=business_id,
        run_id=run_id,
        caption=caption,
        mutation_mode=str(data.get("mutation_mode") or "conservative"),
        skin=skin,
        seed=seed,
        scenes=scenes,
    )


def _packet_lines(doc: dict) -> tuple[str, str]:
    from kleos.core.creative.draft import packet_context
    from kleos.core.substance.contracts import SubstancePacket

    packet = SubstancePacket.model_validate(doc["packet"])
    return packet_context(packet)


def _piece_material(doc: dict) -> tuple[str, str, str | None]:
    variants = doc.get("variants") or []
    variant = variants[0] if variants else {}
    piece = doc.get("piece") or {}
    hook = piece.get("hook") or variant.get("hook") or ""
    narrative = piece.get("narrative") or variant.get("narrative") or ""
    cta = piece.get("cta") or variant.get("cta")
    return hook, narrative, cta


class _PromptHolder:
    def __init__(self) -> None:
        self._registry: Any = None

    def registry(self) -> Any:
        if self._registry is None:
            from kleos.prompts import PromptRegistry, PromptTemplate

            self._registry = PromptRegistry()
            self._registry.register(
                PromptTemplate(
                    id="motion/plan-video",
                    text=_PLAN_PROMPT_TEXT,
                    description="Motion: draft a semantic video plan (scenes + roles)",
                    version=1,
                    task_class="normal",
                )
            )
        return self._registry


_PROMPTS = _PromptHolder()

_PLAN_PROMPT_TEXT = """You are a short-form motion-graphics video planner. Turn one
content piece into a semantic video plan: a chosen motion format and a sequence of
5 to 6 short scenes. Each scene states WHICH WORDS appear on screen and its job
(role). You do NOT do layout, timing or colors — deterministic code does that.

Use only these scene roles: HOOK, ORIENT, CLAIM, COMPARE, EXPLAIN, PROVE, BUILD,
REVEAL, TRANSITION, PAYOFF, CTA. Open with a HOOK scene. Close with a PAYOFF or
CTA scene. Keep every on-screen line SHORT and spoken-natural (one line of a few
words; the hero line ~2 to 8 words) so it reads in 1-2 seconds. Ground every line
in the ALLOWED material below; never assert FORBIDDEN; do not invent facts or
numbers.

Return ONLY a JSON object with exactly these keys:
- format_id: one of f03_kinetic_type, editorial_reviews, tech_cards
- scenes: an array of 5 to 6 objects; each has: id (s01..), role (one of the list),
  primary (the main on-screen line), kicker (optional short lead-in above, or null),
  note (optional muted support line below, or null)

CRAFT RULES (apply; do not reproduce verbatim):
{craft}

CONTENT TO PLAN (ground everything here):
Hook: {hook}
Message: {narrative}
CTA: {cta}

ALLOWED (may assert):
{allowed}

FORBIDDEN (must NOT assert):
{forbidden}
"""


def plan_for_piece(
    doc: dict,
    model: Callable[[str, str], str],
    *,
    format_id: str = "f03_kinetic_type",
    skin: StyleSkin | str | None = None,
    seed: int = 0,
    craft_brief: str | None = None,
    task_class: str | None = None,
    role: str | None = None,
) -> SemanticVideoPlan:
    """Draft a semantic video plan for a stored piece via one routed model call.

    ``skin`` may be a :class:`StyleSkin`, a named skin (``dark_editorial`` /
    ``light_premium`` / ``dark_tech``), or None for the format's default. The
    plan is validated loudly: a malformed or out-of-bounds draft never reaches
    the compiler.
    """
    from kleos import data_policy
    from kleos.jsoncalls import call_json

    allowed, forbidden = _packet_lines(doc)
    hook, narrative, cta = _piece_material(doc)
    guidance = craft_brief if craft_brief is not None else motion_craft_brief()
    prompt = (
        _PROMPTS.registry()
        .render(
            "motion/plan-video",
            {
                "craft": guidance or "(none supplied — apply standard motion craft)",
                "hook": hook or "(no hook)",
                "narrative": narrative or "(no message)",
                "cta": cta or "(no cta)",
                "allowed": allowed,
                "forbidden": forbidden,
            },
        )
        .text
    )
    data = call_json(
        model,
        task_class or "normal",
        prompt,
        role=role,
        data_class=data_policy.for_area("motion_plan"),
    )
    if not isinstance(data, dict):
        raise TypeError("video-plan draft did not return a JSON object")
    chosen = str(data.get("format_id") or format_id or "").strip()
    if chosen not in FORMAT_RECIPES:
        raise ValueError(f"model chose unknown format {chosen!r}; have {sorted(FORMAT_RECIPES)}")
    resolved = default_skin_for(chosen) if skin is None else resolve_skin(skin)
    return plan_from_data(
        {**data, "format_id": chosen},
        skin=resolved,
        seed=seed,
        business_id=doc.get("business_id"),
        run_id=doc.get("run_id"),
    )
