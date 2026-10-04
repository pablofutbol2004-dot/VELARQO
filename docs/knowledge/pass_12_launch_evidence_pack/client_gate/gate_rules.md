# Gate rules

Allowed statuses: `PASS`, `FAIL`, `OPEN`, `NOT_APPLICABLE`.

- `PASS` requires a concrete evidence reference.
- `FAIL` blocks launch.
- `OPEN` blocks launch.
- `NOT_APPLICABLE` is allowed only for a genuinely inapplicable conditional control, with a note explaining why.

A row marked `waivable=NO` cannot be bypassed in the checker.

Rows marked `waivable=YES` are **not casually waivable**; they are conditional controls (mainly AI) that can be `NOT_APPLICABLE` only when the corresponding functionality is not used.

Run:

```bash
python tools/check_client1_gate.py client_gate/client1_gate.csv
```

The script exits non-zero if the campaign is not ready.
