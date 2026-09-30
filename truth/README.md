# Sources of truth

What the business actually is right now: offers, niches, identity and the
rules we operate under. Code and copy read from here, and
`tests/integration/test_truth.py` fails if they drift apart.

Split by side, per `CLAUDE.md`. Never mix the two.

```
truth/
  velarqo/            Velarqo's own business (we sell to trade businesses)
    company.yaml        legal entity + sender identity for our outreach
    offers.yaml         what we sell to trade businesses
    niches.yaml         which trades we target, and with which offer
    compliance.yaml     rules that apply to our own outreach
  clients/
    _template/        copy to clients/<client-id>/ when a client signs
      client.yaml       who they are, their sender identity, our DPA with them
      offers.yaml       what the client offers ITS customers
      segments.yaml     the client's customer segments
      compliance.yaml   consent basis for the client's customer list
  compliance/
    uk.yaml           the law itself: each rule, its source, when last checked
```

## Rules

- `TODO` means a fact only the owner can supply. Nothing that reads a
  `TODO` value may send anything.
- Every law entry has a `source` and a `last_checked` date. Re-check
  anything older than 6 months before relying on it.
- An offer is `live`, `test` or `retired`. Only `live` and `test` offers may
  be used in copy.
- Changing an offer here means changing the copy that uses it; the test
  tells you where.
