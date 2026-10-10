"""Pilot and homeowner state rules (docs/delivery/WORKFLOW.md sections 2-3).
Pure functions, so they're easy to test and reuse."""

PILOT_FLOW = [
    "draft", "sample_received", "audited", "agreement_signed", "data_received",
    "eligibility_frozen", "messages_approved", "canary_ready", "canary_running",
    "canary_reviewed", "live", "completed",
]

# Moves that need an approval row first: (from, to) -> gate.
GATES = {
    ("audited", "agreement_signed"): "agreement",
    ("eligibility_frozen", "messages_approved"): "messages",
    ("canary_ready", "canary_running"): "canary_go",
    ("canary_reviewed", "live"): "go_live",
    ("paused", "live"): "resume",
}


def allowed_pilot_moves(state: str) -> set[str]:
    if state in ("completed", "cancelled"):
        return set()
    moves = {"cancelled"}
    if state == "paused":
        return moves | {"live", "completed"}
    i = PILOT_FLOW.index(state)
    if i + 1 < len(PILOT_FLOW):
        moves.add(PILOT_FLOW[i + 1])
    if state in ("canary_running", "live"):
        moves.add("paused")
    return moves


# Homeowner states, in the only order they may move. A late or repeated
# webhook can't move someone backwards; opted_out beats everything.
_RANK = {s: i for i, s in enumerate([
    "imported", "eligible", "treatment", "queued", "pushing", "push_failed", "enrolled",
    "replied", "booked", "no_show", "attended", "requoted", "lost", "won",
])}
TERMINAL = {"excluded", "holdout", "no_response", "opted_out", "won", "lost"}


def can_move_homeowner(current: str, new: str) -> bool:
    if current == new:
        return False
    if new == "opted_out":
        return current != "opted_out"
    if current in ("excluded", "holdout", "opted_out"):
        return False
    if new in ("excluded", "holdout"):
        return current in ("imported", "eligible")
    if new == "no_response":
        return current == "enrolled"
    if current == "push_failed" and new == "pushing":
        return True                                   # retry after a fixed error
    if current in ("no_response",) or new not in _RANK or current not in _RANK:
        return False
    return _RANK[new] > _RANK[current]
