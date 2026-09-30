"""Read the sources of truth in truth/.

Two sides, never mixed (see CLAUDE.md): velarqo() is Velarqo's own business,
client(client_id) is one signed client. "TODO" marks a fact the owner hasn't
supplied yet; todos() lists them so nothing sends on a missing fact.
"""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
TRUTH = ROOT / "truth"
TODO = "TODO"


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


def _load_dir(folder: Path) -> dict:
    return {p.stem: _load(p) for p in sorted(folder.glob("*.yaml"))}


def velarqo() -> dict:
    return _load_dir(TRUTH / "velarqo")


def client(client_id: str) -> dict:
    folder = TRUTH / "clients" / client_id
    if not folder.is_dir():
        raise FileNotFoundError(f"no truth folder for client {client_id!r}: {folder}")
    return _load_dir(folder)


def client_ids() -> list[str]:
    return sorted(p.name for p in (TRUTH / "clients").iterdir() if p.is_dir() and not p.name.startswith("_"))


def laws() -> dict:
    """Every rule from every jurisdiction file in truth/compliance/, by id."""
    rules = {}
    for path in sorted((TRUTH / "compliance").glob("*.yaml")):
        doc = _load(path)
        for rule in doc["rules"]:
            rules[rule["id"]] = {**rule, "jurisdiction": doc["jurisdiction"]}
    return rules


def offer(offer_id: str) -> dict:
    for o in velarqo()["offers"]["offers"]:
        if o["id"] == offer_id:
            return o
    raise KeyError(f"unknown Velarqo offer {offer_id!r}")


def niche(niche_id: str) -> dict:
    for n in velarqo()["niches"]["niches"]:
        if n["id"] == niche_id:
            return n
    raise KeyError(f"unknown Velarqo niche {niche_id!r}")


def niche_pitch(niche_id: str) -> str:
    """The approved offer line for a niche, in ICP offer_line form ({trade} left in)."""
    n = niche(niche_id)
    return offer(n["offer"])["pitch"].replace("{result}", n["result_noun"])


def niche_icp(niche_id: str) -> dict:
    return json.loads((ROOT / niche(niche_id)["icp_template"]).read_text())


def todos(data, path: str = "") -> list[str]:
    """Dotted paths of every value still set to TODO."""
    if data == TODO:
        return [path]
    if isinstance(data, dict):
        return [t for k, v in data.items() for t in todos(v, f"{path}.{k}" if path else str(k))]
    if isinstance(data, list):
        return [t for i, v in enumerate(data) for t in todos(v, f"{path}[{i}]")]
    return []
