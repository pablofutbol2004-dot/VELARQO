# Worker contracts

Run workers on the VPS (or equivalent durable compute). Supabase/Postgres stores state; workers perform bounded jobs.

## Workers

### `discover_companies`
Writes DISCOVERED candidates + source evidence. Idempotent on source record id / company number.

### `resolve_entity`
Matches Companies House legal entity and company type/status. Unknown stays REVIEW rather than guessed.

### `qualify_company`
Reads current evidence, writes ICP decision with versioned rules.

### `resolve_people_contacts`
Creates people/contact candidates with provenance.

### `verify_contacts`
Calls verification adapter; never deletes old verification evidence.

### `route_compliance`
Evaluates subscriber/entity class, suppression and required transparency/opt-out controls.

### `score_and_cohort`
Calculates score then freezes experiment membership.

### `enqueue_sequence`
Creates idempotent send_queue rows only from records passing every hard gate.

### `send_due`
Atomically claims due queue rows, rechecks suppression immediately before send, then calls sender adapter.

### `ingest_replies`
Writes inbound event, classifies or flags for review, and applies suppression synchronously for objections/unsubscribes.

### `weekly_learning`
Builds acquisition → conversation → export/pilot funnel and feeds evidence back into ICP/contact-source decisions.

## Safety pattern

Before each outbound send:
1. load current canonical contact/company
2. recheck suppression
3. recheck campaign active
4. recheck no live reply/conversation since queue creation
5. acquire idempotency lock
6. send once
7. persist provider result
