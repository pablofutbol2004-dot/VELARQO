"""KLEOS knowledge-library loader — engine-level know-how, all areas.

The knowledge library lives as packs under ``kleos/<area>/<pack>/`` (each pack
holds ``essentials.yaml`` plus a reference map). ``kleos/craft`` is the loader
for the whole library, not only the craft area: it finds every pack by recursive
discovery across all top-level areas (craft, business_mechanics, formats,
assets, distribution, economics, intelligence, growth, delivery, strategy,
ai_systems), keyed by the pack's declared ``pack`` id rather than by folder name.

A piece of content loads the PACKS it needs (``craft_compose``), not one
omniscient pack: a short-form video might load ``hooks + storytelling +
spoken_writing + packaging + cta_conversion + short_form_video``. A business
pack decides which formats it runs; nothing here is business-specific. Typed
YAML loaded into pydantic; see ``kleos/craft/README.md`` for the area/package
map and authoring rules.
"""

from __future__ import annotations

import pathlib
import re
from collections.abc import Sequence

import yaml
from pydantic import BaseModel, Field

_CRAFT_DIR = pathlib.Path(__file__).resolve().parent

#: Hard cap on craft context per model call (deterministic; prevents overfeeding).
#: ~14k chars is roughly 3-4k tokens worst case — enough for the highest-priority
#: packs, and the tail past the budget is dropped, not truncated mid-rule.
CRAFT_MAX_CHARS = 14_000

#: Top-level directories under the library root that are NOT knowledge areas
#: (business packs, gear code, CLI, adapters, bytecode caches).
_NON_PACK_TOP_DIRS = frozenset({"adapters", "business_packs", "console", "core", "__pycache__"})

_KNOWN_AREAS = (
    "craft",
    "business_mechanics",
    "formats",
    "assets",
    "distribution",
    "economics",
    "intelligence",
    "growth",
    "delivery",
    "strategy",
    "ai_systems",
    "motion",
    "carousel",
)


class CraftRule(BaseModel):
    """One prescriptive craft rule from the distilled source material."""

    rule: str = Field(min_length=1)
    why: str | None = None
    source: str | None = None  # provenance tag from the reference map


class CraftPack(BaseModel):
    """A validated craft pack (the ``essentials.yaml`` shape)."""

    schema_version: str = "1"
    pack: str = Field(min_length=1)
    kind: str = "format"  # area-ish tag; e.g. "general" | "format" | "economics" …
    title: str | None = None
    categories: dict[str, list[CraftRule]] = Field(default_factory=dict)


class PackEntry(BaseModel):
    """One discovered knowledge pack: where it lives and its head fields.

    ``pack`` is the canonical id (may differ from the folder name — e.g. the
    ``ai_systems`` pack lives at ``ai_systems/core/``). ``path`` is the canonical
    ``essentials.yaml`` location. Rules are loaded lazily via ``load_craft_pack``.
    """

    pack: str
    branch: str
    path: pathlib.Path
    kind: str
    title: str | None = None
    schema_version: str = "1"


def craft_root() -> pathlib.Path:
    return _CRAFT_DIR


def knowledge_root() -> pathlib.Path:
    """The library root: every sibling knowledge area sits directly under it."""
    return _CRAFT_DIR.parent


def business_mechanics_root() -> pathlib.Path:
    """Sibling area: business-mechanics packs (offer_framing, qualification…)."""
    return _CRAFT_DIR.parent / "business_mechanics"


def formats_root() -> pathlib.Path:
    """Sibling area: literal format packs (landing_page, …), kind ``format``."""
    return _CRAFT_DIR.parent / "formats"


def assets_root() -> pathlib.Path:
    """Sibling area: asset-class packs (lead_magnet, …), kind ``asset_class``."""
    return _CRAFT_DIR.parent / "assets"


def distribution_root() -> pathlib.Path:
    """Sibling area: distribution packs (distribution_through_people, …)."""
    return _CRAFT_DIR.parent / "distribution"


#: (root, tree-signature) -> {pack id: PackEntry}. The signature is the set of
#: pack files found by the inventory walk, so it changes only when packs are
#: added/removed/renamed — never on a content edit, which keeps the index fresh
#: cheaply while per-file mtime/size caching (``_pack_cache``) handles content.
#: Rebuilds are rare and read each essentials.yaml once.
_discovery_cache: dict[tuple[pathlib.Path, tuple], dict[str, PackEntry]] = {}

#: name -> (mtime_ns, size, path, validated pack). Knowledge packs are static,
#: validated YAML read once per model call today; memoizing removes the repeated
#: parse while still refreshing when the file changes (keyed on mtime, not frozen).
_pack_cache: dict[str, tuple[int, int, str, CraftPack]] = {}


def _iter_pack_essentials(root: pathlib.Path):
    """Yield ``(branch, pack_dir, essentials_path)`` for every knowledge pack."""
    for branch_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if branch_dir.name in _NON_PACK_TOP_DIRS:
            continue
        for pack_dir in sorted(p for p in branch_dir.iterdir() if p.is_dir()):
            essentials = pack_dir / "essentials.yaml"
            if essentials.is_file():
                yield branch_dir.name, pack_dir, essentials


def _tree_signature(inventory: list[tuple[str, pathlib.Path, pathlib.Path]]) -> tuple:
    """Structural signature of the pack tree: which pack files exist, and where.

    Built from the ``essentials.yaml`` inventory itself, deliberately NOT from
    directory mtimes. Filesystems (Windows in particular) update a directory's
    mtime lazily, so a pack file added or removed since the last walk could
    otherwise leave a stale discovery cache and report the wrong library.

    File mtimes are excluded on purpose: editing a pack's *content* must not
    invalidate the index. Per-file content freshness is ``_pack_cache``'s job in
    ``load_craft_pack``.
    """
    return tuple(
        (branch, pack_dir.name, str(essentials)) for branch, pack_dir, essentials in inventory
    )


def _discover(root: pathlib.Path | None = None) -> dict[str, PackEntry]:
    """Index every knowledge pack under the root, keyed by its ``pack`` id.

    Recursive over the area folders, not a hard-coded branch list: a new area
    simply needs to add ``<area>/<pack>/essentials.yaml``. Duplicate ``pack``
    ids fail loudly at discovery time (never silently shadowed).

    The walk runs on every call (cheap: one listing pass over the area folders);
    the expensive YAML parse runs only when the pack inventory actually changed.
    """
    root = pathlib.Path(root) if root is not None else knowledge_root()
    inventory = list(_iter_pack_essentials(root))
    signature = _tree_signature(inventory)
    cached = _discovery_cache.get((root, signature))
    if cached is not None:
        return cached
    entries: dict[str, PackEntry] = {}
    for branch, pack_dir, essentials in inventory:
        raw = yaml.safe_load(essentials.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise TypeError(f"knowledge pack must map to an object: {essentials}")
        pack_id = str(raw.get("pack") or "").strip()
        if not pack_id:
            raise ValueError(f"knowledge pack missing a non-empty 'pack' id: {essentials}")
        previous = entries.get(pack_id)
        if previous is not None:
            raise RuntimeError(f"duplicate pack id {pack_id!r}: {previous.path} and {essentials}")
        entries[pack_id] = PackEntry(
            pack=pack_id,
            branch=branch,
            path=essentials,
            kind=str(raw.get("kind") or ""),
            title=raw.get("title"),
            schema_version=str(raw.get("schema_version") or "1"),
        )
    _discovery_cache[(root, signature)] = entries
    return entries


def discover_library(*, _root: pathlib.Path | None = None) -> list[PackEntry]:
    """All knowledge packs, ordered by (branch, pack id). Rules are not loaded."""
    root = pathlib.Path(_root) if _root is not None else knowledge_root()
    return sorted(_discover(root).values(), key=lambda entry: (entry.branch, entry.pack))


def _resolve_pack(name: str, root: pathlib.Path | None = None) -> PackEntry:
    entry = _discover(root).get(name)
    if entry is None:
        areas = ", ".join(_KNOWN_AREAS)
        raise FileNotFoundError(
            f"no craft pack {name!r} under the knowledge library (areas: {areas})"
        )
    return entry


def load_craft_pack(name: str, *, _root: pathlib.Path | None = None) -> CraftPack:
    """Load and validate a knowledge pack from any area by its ``pack`` id.

    Areas are discovered recursively (``craft``, ``business_mechanics``,
    ``formats``, ``assets``, ``distribution``, ``economics``, ``intelligence``,
    ``growth``, ``delivery``, ``strategy``, ``ai_systems``). Packs carry a
    ``kind`` that reflects their home area or function.

    Parsed results are cached per pack and refreshed whenever the underlying
    file changes, so repeated composition (which happens before every model
    call) does not re-read + re-validate the same YAML.
    """
    root = pathlib.Path(_root) if _root is not None else None
    entry = _resolve_pack(name, root)
    stat = entry.path.stat()
    signature = (stat.st_mtime_ns, stat.st_size)
    cached = _pack_cache.get(name)
    if cached is not None and cached[:2] == signature and cached[2] == str(entry.path):
        return cached[3]
    raw = yaml.safe_load(entry.path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise TypeError(f"pack must map to an object: {entry.path}")
    pack = CraftPack.model_validate(raw)
    _pack_cache[name] = (*signature, str(entry.path), pack)
    return pack


def _fit(text: str, max_chars: int | None) -> str:
    """Cut to a character budget at a line boundary (never mid-rule)."""
    if max_chars is None or len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit("\n", 1)[0]


def craft_brief(
    name: str, *, categories: Sequence[str] | None = None, max_chars: int | None = None
) -> str:
    """Compact prompt-context text from selected categories of a craft pack.

    With no ``categories`` given, all categories present in the pack are used (in
    file order). Returns an empty string when the pack has no rules.
    """
    pack = load_craft_pack(name)
    chosen = list(categories) if categories is not None else list(pack.categories)
    lines: list[str] = []
    for category in chosen:
        rules = pack.categories.get(category)
        if not rules:
            continue
        lines.append(f"[{category}]")
        for item in rules:
            line = f"- {item.rule}"
            if item.why:
                line = f"{line} — {item.why}"
            lines.append(line)
    return _fit("\n".join(lines), max_chars)


def craft_compose(
    names: Sequence[str],
    *,
    categories: Sequence[str] | None = None,
    max_chars: int | None = None,
) -> str:
    """Join the briefs of several packs so a piece loads exactly what it needs.

    A short-form video might compose ``hooks, storytelling, spoken_writing,
    packaging, cta_conversion, short_form_video``. Fails loudly on an unknown
    pack — composing with a missing pack is a configuration error. When
    ``max_chars`` is given the result is capped at a line boundary (the tail is
    dropped, keeping the higher-priority packs/categories that came first).
    """
    parts: list[str] = []
    for name in names:
        parts.append(craft_brief(name, categories=categories, max_chars=max_chars))
    return _fit("\n\n".join(p for p in parts if p), max_chars)


#: Which general packs a format slice composes by default when drafting, so the
#: general knowledge is actually consumed (never sitting as unused reference).
GENERAL_PACKS_FOR_FORMAT: dict[str, tuple[str, ...]] = {
    "short_form_video": (
        "hooks",
        "storytelling",
        "spoken_writing",
        "value_communication",
        "cta_conversion",
        "proof",
    ),
}


def compose_format_bundle(
    format_name: str,
    *,
    extra: Sequence[str] | None = None,
    max_chars: int | None = CRAFT_MAX_CHARS,
) -> tuple[str, list[str]]:
    """The craft brief a format slice should draft with: the format pack plus the
    general packs that apply to it.

    Returns ``(brief_text, packs_included)``. General packs that do not exist yet
    are skipped (the library grows over time); the format pack itself must exist.
    The brief is capped at ``max_chars`` (default :data:`CRAFT_MAX_CHARS`) so a
    prompt is never overfed; priority order is the format pack first, then the
    general packs.
    """
    wanted = [format_name, *(GENERAL_PACKS_FOR_FORMAT.get(format_name, ())), *(extra or ())]
    present: list[str] = []
    for name in wanted:
        try:
            load_craft_pack(name)
        except FileNotFoundError:
            continue  # a general pack may not exist yet; enrich when it lands
        present.append(name)
    if not present:
        raise FileNotFoundError(f"no craft pack for format {format_name!r}")
    return craft_compose(present, max_chars=max_chars), present


#: Which general packs a pipeline PHASE reads (as opposed to a format slice).
#: These are the consumers that stop packs from being unused reference:
PHASE_PACKS: dict[str, tuple[str, ...]] = {
    "strategy": (
        "ideation_angles",  # choosing what/which angle before writing
        "buyer_awareness",  # matching the message to the buyer's current awareness
    ),
    "draft": (  # writing creative variants (any format)
        "attention",
        "copywriting",
        "hooks",
        "storytelling",
        "spoken_writing",
        "value_communication",
        "proof",
    ),
    "quality": ("content_quality",),  # judging a finished draft (craft audit)
    "measure": ("content_measurement",),  # reading results / deciding what to test
}


def compose_phase_bundle(
    phase: str,
    *,
    extra: Sequence[str] | None = None,
    max_chars: int | None = CRAFT_MAX_CHARS,
) -> tuple[str, list[str]]:
    """The craft brief a pipeline phase should load (e.g. Strategy -> ideation).

    General packs that do not exist yet are skipped; the phase must be a known
    key in :data:`PHASE_PACKS` or provide ``extra`` packs. The brief is capped at
    ``max_chars`` so a step never overfeeds its prompt.
    """
    wanted = [*(PHASE_PACKS.get(phase, ())), *(extra or ())]
    present: list[str] = []
    for name in wanted:
        try:
            load_craft_pack(name)
        except FileNotFoundError:
            continue
        present.append(name)
    return craft_compose(present, max_chars=max_chars), present


def _normalized_rule(text: str) -> str:
    """Normalize a rule for exact-duplicate detection (whitespace only)."""
    return re.sub(r"\s+", " ", text.strip())


def validate_library(*, _root: pathlib.Path | None = None) -> dict:
    """Validate every knowledge pack; raise loudly on any structural problem.

    Checks (per prompt contract) that every pack: parses; carries the required
    head fields; belongs to exactly one area; has no empty categories; and that
    no exact rule text is duplicated across different packs. Returns counts.
    """
    root = pathlib.Path(_root) if _root is not None else knowledge_root()
    loaded: list[tuple[PackEntry, CraftPack]] = []
    for entry in discover_library(_root=root):
        if not entry.pack:
            raise RuntimeError(f"empty pack id at {entry.path}")
        if not entry.branch:
            raise RuntimeError(f"pack {entry.pack!r} has no home area")
        if not entry.kind:
            raise RuntimeError(f"pack {entry.pack!r} is missing its 'kind' field")
        if entry.schema_version != "1":
            raise RuntimeError(
                f"pack {entry.pack!r} has unsupported schema_version {entry.schema_version!r}"
            )
        pack = load_craft_pack(entry.pack, _root=root)
        if not pack.categories:
            raise RuntimeError(f"pack {entry.pack!r} has no categories")
        for category, rules in pack.categories.items():
            if not rules:
                raise RuntimeError(f"pack {entry.pack!r} category {category!r} is empty")
        loaded.append((entry, pack))

    # Exact duplicate rule text across canonical packs (never silently merged).
    owner_of: dict[str, str] = {}
    duplicates: list[tuple[str, str, str]] = []
    for entry, pack in loaded:
        for rules in pack.categories.values():
            for rule in rules:
                key = _normalized_rule(rule.rule)
                if key in owner_of and owner_of[key] != entry.pack:
                    duplicates.append((rule.rule, owner_of[key], entry.pack))
                else:
                    owner_of.setdefault(key, entry.pack)
    if duplicates:
        rule, first, second = duplicates[0]
        raise RuntimeError(
            f"duplicate rule text across packs ({len(duplicates)} total); "
            f"first: {rule!r} in {first!r} and {second!r}"
        )

    by_branch: dict[str, dict[str, int]] = {}
    total_rules = 0
    for entry, pack in loaded:
        rules = sum(len(rules) for rules in pack.categories.values())
        total_rules += rules
        bucket = by_branch.setdefault(entry.branch, {"packs": 0, "rules": 0})
        bucket["packs"] += 1
        bucket["rules"] += rules
    return {
        "packs": len(loaded),
        "rules": total_rules,
        "areas": sorted(by_branch),
        "by_area": by_branch,
    }


def library_report_text(*, _root: pathlib.Path | None = None) -> str:
    """Plain-text library report: validates loudly, then prints pack/rule counts."""
    root = pathlib.Path(_root) if _root is not None else None
    info = validate_library(_root=root)
    lines = [
        "KLEOS knowledge library",
        "=======================",
        f"packs: {info['packs']}   rules: {info['rules']}   areas: {len(info['areas'])}",
    ]
    for area in info["areas"]:
        bucket = info["by_area"][area]
        lines.append(f"  {area}: {bucket['packs']} packs / {bucket['rules']} rules")
    return "\n".join(lines)
