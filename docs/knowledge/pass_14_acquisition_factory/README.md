# Pass 14 — Acquisition Factory

Purpose: turn a raw UK company universe into a clean, evidence-backed, compliant, scored and measurable outbound queue without binding Velarqo to one enrichment or sending vendor.

Pipeline:

`DISCOVERED → ENTITY_VERIFIED → COMPANY_QUALIFIED → WEBSITE_RESOLVED → PERSON_RESOLVED → CONTACT_RESOLVED → COMPLIANCE_ROUTED → EMAIL_VERIFIED → SCORED → COHORTED → READY_TO_SEND → SENT → REPLIED → CONVERSATION → EXPORT → PILOT`

This pack is deliberately provider-agnostic. Companies House, FENSA/Certass, search engines, company websites, Hunter, Apollo and other services are adapters that populate canonical records; none owns the canonical record.

## Non-negotiables

1. Discovery is not permission to contact.
2. Never infer legal entity type from a domain/email alone when it can be verified.
3. A person's email is personal data even when used in a business context.
4. Suppression is permanent across imports unless a documented lawful reason says otherwise.
5. No send queue without source provenance and a compliance route.
6. One canonical company/person/contact identity; adapters may disagree.
7. Every transformation is idempotent and re-runnable.
8. Replies and negative feedback update future targeting, not just the current campaign.
9. Sending infrastructure and contact-data logic are separate systems.
10. Optimize for qualified conversations and downstream revenue, not list size.

## Included

- architecture/state_machine.md
- architecture/data_model.md
- playbooks/01_universe_discovery.md
- playbooks/02_identity_dedupe.md
- playbooks/03_company_qualification.md
- playbooks/04_decision_maker_resolution.md
- playbooks/05_contact_resolution_verification.md
- playbooks/06_compliance_routing.md
- playbooks/07_scoring_cohorts.md
- playbooks/08_send_queue.md
- playbooks/09_reply_feedback_loop.md
- playbooks/10_quality_control.md
- schemas/*.csv
- tools/normalize_companies.py
- tools/route_compliance.py
- tools/build_send_queue.py
- tools/audit_factory.py
- sources/current_sources.md
- examples/*

## Relationship to earlier passes

Pass 13 defines the first-10-installers sprint and 20-control outbound-readiness gate. Pass 14 supplies the factory underneath it. Pass 12 remains the separate 50-control Client-1/homeowner-data gate.
