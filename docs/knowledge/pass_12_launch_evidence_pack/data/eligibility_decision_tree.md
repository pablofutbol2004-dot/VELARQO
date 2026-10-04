# Contact eligibility decision tree

For each row, stop at the first failing condition and record the reason.

1. **Stable identity:** can this contact/quote be uniquely tracked?
2. **Suppression:** prior objection/opt-out? → exclude.
3. **Current state:** already won/current customer/active opportunity that should not be disturbed? → exclude or route separately.
4. **Product:** campaign is for the client's own similar product/service? If no → exclude.
5. **Provenance:** source and collection context sufficiently known for the chosen route? If no → do not market until resolved.
6. **PECR/data basis:** chosen communication route supported? If no → exclude.
7. **Privacy information:** required notice path defined? If no → block until defined.
8. **Reachability/data quality:** usable channel? If no → mark unreachable, do not improvise identity.
9. **Operational fit:** geography/product/time window still serviceable? If no → exclude.
10. **Experiment assignment:** eligible contact assigned to test/holdout deterministically and only once.

Do not “clean” unknown provenance into apparent eligibility.
