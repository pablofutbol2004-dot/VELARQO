"""Pilot and homeowner state rules (docs/delivery/WORKFLOW.md sections 2-3).
Pure functions, so they're easy to test and reuse."""

PILOT_FLOW = [
    "draft", "sample_received", "audited", "agreement_signed", "data_received",
    "eligibility_frozen", "messages_approved", "canary_ready", "canary_running",
    "canary_reviewed", "live", "completed",
]
SENDING = ("canary_running", "live")
# A person excluded for one of these on ANY of their quotes is excluded on all.
PERSON_WIDE_REASONS = ("opted out", "on client's do-not-contact list", "already won/booked")

# Moves that need an approval row first: (from, to) -> gate.
GATES = {
    ("audited", "agreement_signed"): "agreement",
    ("eligibility_frozen", "messages_approved"): "messages",
    ("canary_ready", "canary_running"): "canary_go",
    ("canary_reviewed", "live"): "go_live",
    ("paused", "canary_running"): "resume",
    ("paused", "live"): "resume",
}


def allowed_pilot_moves(state: str, paused_from: str | None = None) -> set[str]:
    """A paused pilot can only go back to the sending state it was paused
    from (so a paused canary can't skip the go-live gate), or end."""
    if state in ("completed", "cancelled"):
        return set()
    moves = {"cancelled"}
    if state == "paused":
        return moves | {"completed", paused_from or "live"}
    i = PILOT_FLOW.index(state)
    if i + 1 < len(PILOT_FLOW):
        moves.add(PILOT_FLOW[i + 1])
    if state in SENDING:
        moves.add("paused")
    return moves


# Homeowner states, in the only order they may move. A late or repeated
# webhook can't move someone backwards; opted_out beats everything.
_RANK = {s: i for i, s in enumerate([
    "imported", "eligible", "treatment", "queued", "pushing", "push_failed", "enrolled",
    "replied", "booked", "no_show", "attended", "requoted", "lost", "won",
])}
TERMINAL = {"excluded", "holdout", "no_response", "opted_out", "won", "lost"}
PAST_ENROLLED = {"replied", "booked", "no_show", "attended", "requoted", "won", "lost", "no_response", "opted_out"}


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
    if current == "no_show" and new == "booked":
        return True                                   # rebooked after a no-show or cancellation
    if current == "no_response" or new not in _RANK or current not in _RANK:
        return False
    return _RANK[new] > _RANK[current]
