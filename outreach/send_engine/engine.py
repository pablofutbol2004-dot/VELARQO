"""Database side of Velarqo's own cold outreach (Supabase Postgres).

Flow: create_cohort (draft campaign + step-1 messages) -> human reviews the
exported CSV -> activate -> run: sync_inbox, schedule_followups,
check_stop_rules, send_due.

Safety properties:
- A message is claimed ('sending') and committed *before* the provider is
  called. A crash mid-send leaves it in 'sending' for a human to check; it
  is never retried automatically, so nobody gets the same email twice.
- idempotency_key (campaign:company:step) is unique, so re-running cohort
  creation or follow-up scheduling cannot create a duplicate message.
- Every send re-checks the kill switch, the campaign status, suppressions
  (email and domain), replies from the company, and company type.

Connections must be autocommit; each `with conn.transaction()` block is one
atomic unit. Wrapping a whole run in an outer transaction and rolling it
back gives a safe dry run.
"""

import json
import random
import re
import time as _time
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from integrations.email.base import EmailAuthError, EmailRateLimitError
from outreach.reply_classifier.classify import categorize_reply
from outreach.send_engine import compose, guards

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _event(cur, type_: str, company_id, message_id=None, payload: dict | None = None) -> None:
    cur.execute(
        "insert into events (company_id, message_id, type, payload) values (%s, %s, %s, %s)",
        (company_id, message_id, type_, Jsonb(payload or {})),
    )


# --- Controls -----------------------------------------------------------

def controls(conn) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute("select sending_enabled, paused_reason, updated_at from send_controls").fetchone()


def note_problem(conn, mailbox: str, problem: str) -> None:
    with conn.transaction():
        conn.execute("insert into outbound_problems (mailbox, problem) values (%s, %s)", (mailbox, problem[:1000]))


def recent_problems(conn, hours: int = 24) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            "select mailbox, problem, created_at from outbound_problems where created_at > now() - make_interval(hours => %s) "
            "order by created_at desc limit 20", (hours,)).fetchall()


def set_sending(conn, enabled: bool, reason: str | None = None) -> None:
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            "update send_controls set sending_enabled = %s, paused_reason = %s, updated_at = now()",
            (enabled, None if enabled else reason),
        )
        if not enabled:
            _event(cur, "paused", None, payload={"reason": reason})


def set_campaign_status(conn, campaign_id: str, status: str) -> None:
    allowed_from = {"active": ("draft", "paused"), "paused": ("active",), "done": ("draft", "active", "paused")}
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            "update campaigns set status = %s where id = %s and status = any(%s) returning id",
            (status, campaign_id, list(allowed_from[status])),
        )
        if cur.fetchone() is None:
            raise ValueError(f"campaign {campaign_id} can't move to {status} from its current status")
        if status == "done":
            cur.execute(
                "update messages set status = 'cancelled', skip_reason = 'campaign done' "
                "where campaign_id = %s and status = 'queued'", (campaign_id,),
            )


# --- Cohort creation ----------------------------------------------------

# Boolean outreach_queue columns an experiment may target ("segment") or
# reserve for another test ("exclude_segments"). Whitelisted: they go into SQL.
SEGMENT_COLUMNS = {"no_pressure_sales", "home_survey", "generic_inbox", "accredited", "residential", "runs_ads", "lead_sites"}


def _segment_filter(experiment: dict) -> str:
    clauses = []
    for column in experiment.get("segment") or []:
        if column not in SEGMENT_COLUMNS:
            raise ValueError(f"unknown segment {column!r}")
        clauses.append(f"and q.{column}")
    for column in experiment.get("exclude_segments") or []:
        if column not in SEGMENT_COLUMNS:
            raise ValueError(f"unknown segment {column!r}")
        clauses.append(f"and not coalesce(q.{column}, false)")
    return "\n              ".join(clauses)


def create_cohort(conn, name: str, size: int, experiment: dict, icp: dict, icp_version: str) -> dict:
    """Draft campaign with the top `size` unsent companies from outreach_queue,
    split across the experiment's arms."""
    segment_sql = _segment_filter(experiment)
    with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
        # One email address = one recipient, across every batch and trade:
        # several company rows can share an inbox (group companies, the same
        # firm in windows and roofing), and it must get one sequence only.
        rows = cur.execute(
            f"""
            select * from (
              select distinct on (lower(c.email)) c.id, c.display_name, c.email, c.city, c.extra, c.company_category, q.priority
              from outreach_queue q
              join companies c on c.id = q.id
              where c.company_category = any(%s)
                and c.vertical = %s
                and not (lower(split_part(c.email, '@', 2)) = any(%s))
                and not exists (select 1 from messages m where m.company_id = c.id and m.status <> 'cancelled')
                and not exists (select 1 from messages m where lower(m.to_email) = lower(c.email) and m.status <> 'cancelled')
                and not exists (select 1 from replies r where lower(r.from_email) = lower(c.email))
                {segment_sql}
              order by lower(c.email), q.priority desc, c.id
            ) one_per_address
            order by priority desc, id
            limit %s
            """,
            (sorted(guards.CORPORATE_CATEGORIES), experiment.get("vertical", "windows"),
             sorted(guards.FREE_MAIL_DOMAINS | guards.PLATFORM_DOMAINS), size),
        ).fetchall()
        if not rows:
            return {"campaign_id": None, "messages": 0}

        settings = {
            "icp_version": icp_version,
            "sequence": {"follow_up_gaps_business_days": guards.FOLLOW_UP_GAPS},
            "signature": compose.SIGNATURE,
            "opt_out_line": compose.OPT_OUT_LINE,
            "experiment": experiment,
            "follow_up_templates": compose.FOLLOW_UP_TEMPLATES,
        }
        campaign_id = cur.execute(
            "insert into campaigns (name, vertical, settings, status) values (%s, %s, %s, 'draft') returning id",
            (name, experiment.get("vertical", "windows"), Jsonb(json.loads(json.dumps(settings, default=str)))),
        ).fetchone()["id"]

        # Blocked randomisation: walk the priority-sorted list in blocks of
        # len(arms) and shuffle the arms inside each block. Arms stay balanced
        # on priority (no arm gets the better leads) and on count.
        arms = len(experiment["arms"])
        rng = random.Random(str(campaign_id))
        assignment = []
        while len(assignment) < len(rows):
            block = list(range(arms))
            rng.shuffle(block)
            assignment += block
        created = 0
        for row, arm_index in zip(rows, assignment):
            email = compose.first_touch(row, experiment, arm_index)
            issues = compose.problems(email)
            if issues:
                raise ValueError(f"{row['display_name']}: {', '.join(issues)}")
            message_id = cur.execute(
                """
                insert into messages (campaign_id, company_id, to_email, variant_index, subject, body,
                                      sequence_step, status, scheduled_for, idempotency_key)
                values (%s, %s, %s, %s, %s, %s, 1, 'queued', now(), %s)
                on conflict do nothing
                returning id
                """,
                (campaign_id, row["id"], row["email"], email["variant_index"], email["subject"], email["body"],
                 f"{campaign_id}:{row['id']}:1"),
            ).fetchone()
            if message_id:
                _event(cur, "queued", row["id"], message_id["id"], {"campaign_id": str(campaign_id), "step": 1})
                created += 1
        return {"campaign_id": str(campaign_id), "messages": created}


def review_rows(conn, campaign_id: str) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            select m.id as message_id, c.display_name, m.to_email, c.city, c.website, q.priority,
                   m.sequence_step, m.variant_index, m.status, m.subject, m.body
            from messages m
            join companies c on c.id = m.company_id
            left join outreach_queue q on q.id = c.id
            where m.campaign_id = %s
            order by q.priority desc nulls last, m.sequence_step
            """,
            (campaign_id,),
        ).fetchall()


def cancel_message(conn, message_id: str, reason: str) -> bool:
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            "update messages set status = 'cancelled', skip_reason = %s where id = %s and status = 'queued' "
            "returning company_id", (reason, message_id),
        )
        row = cur.fetchone()
        if row:
            _event(cur, "skipped", row[0], message_id, {"reason": reason})
        return row is not None


# --- Suppression --------------------------------------------------------

def suppress(cur, email: str | None, reason: str, source: str, domain_too: bool = False) -> None:
    if email:
        cur.execute(
            "insert into suppressions (email, reason, source) values (lower(%s), %s, %s) on conflict do nothing",
            (email, reason, source),
        )
    domain = guards.email_domain(email)
    if domain_too and guards.domain_suppressible(domain):
        cur.execute(
            "insert into suppressions (domain, reason, source) values (%s, %s, %s) on conflict do nothing",
            (domain, reason, source),
        )


def _is_suppressed(cur, email: str) -> bool:
    return cur.execute(
        "select 1 from suppressions where lower(email) = lower(%s) or lower(domain) = %s limit 1",
        (email, guards.email_domain(email)),
    ).fetchone() is not None


def _company_has_replied(cur, company_id, address: str | None = None) -> bool:
    """A person (not an auto-reply) answered, from this company or this address."""
    return cur.execute(
        "select 1 from replies where (company_id = %s or lower(from_email) = lower(%s)) "
        "and coalesce(category, '') not in ('out_of_office', 'bounce') limit 1",
        (company_id, address or ""),
    ).fetchone() is not None


def _address_taken(cur, msg: dict) -> bool:
    """Another sequence (other campaign or company row) already emailed this
    exact address: one inbox gets one sequence."""
    return cur.execute(
        "select 1 from messages where lower(to_email) = lower(%s) and status in ('sent', 'sending') "
        "and (campaign_id <> %s or company_id <> %s) and id <> %s limit 1",
        (msg["to_email"], msg["campaign_id"], msg["company_id"], msg["id"]),
    ).fetchone() is not None


# --- Sending ------------------------------------------------------------

def _claim(conn, mailbox: str, statuses: list[str]) -> dict | None:
    with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            update messages set status = 'sending', mailbox = %s
            where id = (
              select m.id from messages m
              join campaigns c on c.id = m.campaign_id
              where m.status = 'queued' and c.status = any(%s)
                and m.scheduled_for <= now()
                and (m.mailbox is null or m.mailbox = %s)
              order by m.sequence_step desc, m.scheduled_for, m.id
              for update of m skip locked
              limit 1
            )
            returning id, campaign_id, company_id, to_email, subject, body, sequence_step, in_reply_to_message_id
            """,
            (mailbox, statuses, mailbox),
        ).fetchone()


def _block_reason(conn, msg: dict) -> str | None:
    with conn.cursor(row_factory=dict_row) as cur:
        if _is_suppressed(cur, msg["to_email"]):
            return "suppressed"
        if not guards.is_company_mailbox(msg["to_email"]):
            return "free-mail or platform address (not a company mailbox)"
        if _company_has_replied(cur, msg["company_id"], msg["to_email"]):
            return "company replied"
        if _address_taken(cur, msg):
            return "address already emailed in another sequence"
        company = cur.execute("select company_category from companies where id = %s", (msg["company_id"],)).fetchone()
        if not company or not guards.is_corporate(company["company_category"]):
            return "not a corporate subscriber"
        if msg["sequence_step"] > 1:
            parent = cur.execute(
                "select status, bounced_at from messages where id = %s", (msg["in_reply_to_message_id"],)
            ).fetchone()
            if not parent or parent["status"] != "sent" or parent["bounced_at"]:
                return "previous step not delivered"
    return None


def _finish(conn, msg: dict, status: str, event: str, **fields) -> None:
    sets = ", ".join(f"{k} = %s" for k in ["status", *fields])
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(f"update messages set {sets} where id = %s", (status, *fields.values(), msg["id"]))
        _event(cur, event, msg["company_id"], msg["id"], {k: str(v) for k, v in fields.items() if k != "sent_at"})


def _thread_of(conn, message_id) -> dict:
    if not message_id:
        return {}
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            "select provider_thread_id, rfc_message_id, provider_message_id from messages where id = %s", (message_id,)
        ).fetchone() or {}


def send_due(conn, provider, mailbox: str, daily_cap: int, max_this_run: int = 8, *,
             require_enabled: bool = True, respect_window: bool = True, campaign_statuses=("active",),
             pause_seconds: tuple[int, int] = (45, 120), sleep=_time.sleep, now=_now) -> dict:
    summary = {"mailbox": mailbox, "sent": 0, "skipped": 0, "failed": 0, "stopped": None}
    if not conn.autocommit and not conn.info.transaction_status:  # dry_run wraps us in a rolled-back transaction on purpose
        raise RuntimeError("send_due needs an autocommit connection: the 'sending' claim must be committed before the provider is called")
    if respect_window and not guards.in_send_window(now()):
        summary["stopped"] = "outside UK send window"
        return summary

    with conn.cursor() as cur:
        sent_today = cur.execute(
            "select count(*) from messages where mailbox = %s and status = 'sent' and sent_at >= %s",
            (mailbox, guards.uk_day_start(now())),
        ).fetchone()[0]
    budget = min(daily_cap - sent_today, max_this_run)
    consecutive_failures = 0

    while budget > 0:
        if require_enabled and not controls(conn)["sending_enabled"]:
            summary["stopped"] = "sending disabled"
            break
        msg = _claim(conn, mailbox, list(campaign_statuses))
        if msg is None:
            break

        reason = _block_reason(conn, msg)
        if reason:
            _finish(conn, msg, "skipped", "skipped", skip_reason=reason)
            summary["skipped"] += 1
            continue

        thread = _thread_of(conn, msg["in_reply_to_message_id"])
        send_kwargs = dict(to=msg["to_email"], subject=msg["subject"], body=msg["body"],
                           thread_id=thread.get("provider_thread_id"), in_reply_to_message_id=thread.get("rfc_message_id"))
        if thread.get("provider_message_id") and getattr(provider, "THREADS_BY_PARENT_ID", False):
            send_kwargs["parent_provider_message_id"] = thread["provider_message_id"]   # Outlook: reply to the parent
        try:
            result = provider.send_email(**send_kwargs)
        except EmailRateLimitError:
            _finish(conn, msg, "queued", "note", skip_reason="rate limited, will retry")
            summary["stopped"] = "provider rate limit"
            break
        except EmailAuthError as exc:
            # The token, not the email, is the problem: put it back and stop this mailbox.
            _finish(conn, msg, "queued", "note", skip_reason="mailbox login refused, will retry")
            summary["stopped"] = f"mailbox login refused ({exc}); re-run authorize-mailbox"
            break
        except Exception as exc:  # noqa: BLE001 - any provider error must be recorded, not crash the run
            _finish(conn, msg, "failed", "failed", skip_reason=f"{type(exc).__name__}: {exc}"[:500])
            summary["failed"] += 1
            consecutive_failures += 1
            if consecutive_failures >= 3:
                summary["stopped"] = "3 consecutive send failures"
                break
            continue

        rfc_id = result.get("rfc_message_id")
        if not rfc_id and hasattr(provider, "rfc_message_id") and result.get("message_id"):
            try:
                rfc_id = provider.rfc_message_id(result["message_id"])
            except Exception:  # noqa: BLE001 - threading info is nice-to-have
                rfc_id = None
        _finish(conn, msg, "sent", "sent", sent_at=now(), provider=type(provider).__name__,
                provider_message_id=result.get("message_id"), provider_thread_id=result.get("thread_id"),
                rfc_message_id=rfc_id)
        summary["sent"] += 1
        consecutive_failures = 0
        budget -= 1
        if budget > 0:
            sleep(random.uniform(*pause_seconds))

    return summary


# --- Follow-ups ---------------------------------------------------------

def schedule_followups(conn, now=_now, campaign_statuses=("active",)) -> int:
    with conn.cursor(row_factory=dict_row) as cur:
        candidates = cur.execute(
            """
            select m.id, m.campaign_id, m.company_id, m.to_email, m.mailbox, m.variant_index,
                   m.sequence_step, m.sent_at, first.subject as first_subject, c.display_name,
                   cp.settings->'experiment' as experiment
            from messages m
            join campaigns cp on cp.id = m.campaign_id
            join companies c on c.id = m.company_id
            join messages first on first.campaign_id = m.campaign_id and first.company_id = m.company_id
                               and first.sequence_step = 1
            where m.status = 'sent' and m.bounced_at is null and m.sequence_step < %s
              and cp.status = any(%s)
              and not exists (select 1 from messages n where n.in_reply_to_message_id = m.id)
            """,
            (guards.LAST_STEP, list(campaign_statuses)),
        ).fetchall()

    created = 0
    for prev in candidates:
        step = prev["sequence_step"] + 1
        if not guards.follow_up_due(prev["sent_at"], step, now()):
            continue
        with conn.transaction(), conn.cursor() as cur:
            if _is_suppressed(cur, prev["to_email"]) or _company_has_replied(cur, prev["company_id"]):
                continue
            arms = (prev["experiment"] or {}).get("arms") or []
            arm = arms[prev["variant_index"] % len(arms)] if arms and prev["variant_index"] is not None else None
            email = compose.follow_up(step, prev, prev["first_subject"], arm)
            cur.execute(
                """
                insert into messages (campaign_id, company_id, to_email, variant_index, subject, body, sequence_step,
                                      status, scheduled_for, mailbox, in_reply_to_message_id, idempotency_key)
                values (%s, %s, %s, %s, %s, %s, %s, 'queued', now(), %s, %s, %s)
                on conflict do nothing
                returning id
                """,
                (prev["campaign_id"], prev["company_id"], prev["to_email"], prev["variant_index"], email["subject"],
                 email["body"], step, prev["mailbox"], prev["id"], f"{prev['campaign_id']}:{prev['company_id']}:{step}"),
            )
            row = cur.fetchone()
            if row:
                _event(cur, "queued", prev["company_id"], row[0], {"step": step})
                created += 1
    return created


# --- Inbox: replies and bounces -----------------------------------------

def _match(cur, mailbox: str, inbound: dict) -> dict | None:
    if inbound.get("thread_id"):
        row = cur.execute(
            "select id, company_id, to_email from messages where mailbox = %s and provider_thread_id = %s "
            "order by sequence_step desc limit 1", (mailbox, inbound["thread_id"]),
        ).fetchone()
        if row:
            return row
    row = cur.execute(
        "select id, company_id, to_email from messages where mailbox = %s and status = 'sent' "
        "and lower(to_email) = %s order by sent_at desc limit 1", (mailbox, inbound["from_email"]),
    ).fetchone()
    if row:
        return row
    # Someone else at the same firm wrote back (info@ forwarded to dave@):
    # match on the sender's company domain, never on shared/free-mail domains.
    domain = guards.email_domain(inbound["from_email"])
    if guards.domain_suppressible(domain):
        return cur.execute(
            "select id, company_id, to_email from messages where mailbox = %s and status = 'sent' "
            "and lower(split_part(to_email, '@', 2)) = %s order by sent_at desc limit 1", (mailbox, domain),
        ).fetchone()
    return None


def record_inbound(conn, mailbox: str, inbound: dict) -> dict:
    verdict = categorize_reply(inbound["from_email"], inbound["subject"], inbound["body"],
                               auto_submitted=inbound.get("auto_submitted", False))
    category = verdict["category"]
    received_at = (datetime.fromtimestamp(inbound["internal_date_ms"] / 1000, timezone.utc)
                   if inbound.get("internal_date_ms") else _now())

    with conn.transaction(), conn.cursor(row_factory=dict_row) as cur:
        msg = _match(cur, mailbox, inbound)
        if msg is None and category == "bounce":
            # Some bounce notices (Outlook NDRs, other MTAs) aren't threaded: find our recipient in the notice text.
            mentioned = sorted({e.lower() for e in _EMAIL.findall(inbound["body"])})
            msg = cur.execute(
                "select id, company_id, to_email from messages where mailbox = %s and status = 'sent' "
                "and lower(to_email) = any(%s) order by sent_at desc limit 1", (mailbox, mentioned),
            ).fetchone()
        needs_human = verdict["needs_human"] or (msg is None and category not in ("bounce", "out_of_office"))
        reply = cur.execute(
            """
            insert into replies (message_id, company_id, from_email, subject, body, sentiment, classification,
                                 provider_message_id, mailbox, category, needs_human, received_at)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            on conflict do nothing
            returning id
            """,
            (msg and msg["id"], msg and msg["company_id"], inbound["from_email"], inbound["subject"][:500],
             inbound["body"][:20000], verdict["sentiment"], Jsonb(verdict), inbound["provider_message_id"],
             mailbox, category, needs_human, received_at),
        ).fetchone()
        if reply is None:
            return {"category": category, "matched": msg is not None, "new": False}
        if msg is None:
            # Can't tie it to an email we sent, but an opt-out is an opt-out:
            # honour it for the sender (and their company domain).
            if verdict["suppress"] and category != "bounce":
                reason = {"complaint": "complained", "not_interested": "dnd"}.get(category, "unsubscribed")
                suppress(cur, inbound["from_email"], reason, f"reply-unmatched:{category}", domain_too=True)
                domain = guards.email_domain(inbound["from_email"])
                cur.execute(
                    "update messages set status = 'cancelled', skip_reason = %s where status = 'queued' "
                    "and (lower(to_email) = %s or (%s and lower(split_part(to_email, '@', 2)) = %s))",
                    (f"inbound {category} (unmatched)", inbound["from_email"], guards.domain_suppressible(domain), domain),
                )
            if category != "complaint":
                return {"category": category, "matched": False, "new": True}
        else:
            company_id, message_id = msg["company_id"], msg["id"]
            if category == "bounce":
                cur.execute("update messages set bounced_at = coalesce(bounced_at, %s) where id = %s", (received_at, message_id))
                _event(cur, "bounced", company_id, message_id)
                suppress(cur, msg["to_email"], "bounced", f"bounce:{mailbox}")
            elif verdict["stops_sequence"]:
                cur.execute(
                    "update messages set replied_at = coalesce(replied_at, %s), reply_sentiment = %s where id = %s",
                    (received_at, verdict["sentiment"], message_id),
                )
                _event(cur, "replied", company_id, message_id, {"category": category})

            if verdict["stops_sequence"]:
                cur.execute(
                    "update messages set status = 'cancelled', skip_reason = %s where status = 'queued' "
                    "and (company_id = %s or lower(to_email) = lower(%s))",
                    (f"inbound {category}", company_id, msg["to_email"]),
                )
            if verdict["suppress"] and category != "bounce":
                reason = {"complaint": "complained", "not_interested": "dnd"}.get(category, "unsubscribed")
                for address in {inbound["from_email"], msg["to_email"].lower()}:
                    suppress(cur, address, reason, f"reply:{category}", domain_too=True)
                _event(cur, "unsubscribed" if category == "unsubscribe" else "suppressed", company_id, message_id,
                       {"category": category})

    if category == "complaint":
        set_sending(conn, False, f"complaint received from {inbound['from_email']} - review before re-enabling")
    return {"category": category, "matched": msg is not None, "new": True}


# Everything received in the last 30 days, wherever it was filed (archived,
# spam, labels): a "no" read and archived before the tick must still count,
# and so must one that arrived while the PC was off for a week. Gmail search
# syntax; the Outlook provider reads only the newer_than:<N>d part of it.
INBOX_QUERY = "in:anywhere -in:sent -in:drafts -in:chats newer_than:30d"


def sync_inbox(conn, provider, mailbox: str, query: str = INBOX_QUERY) -> dict:
    try:
        ids = provider.list_inbox(query, max_results=1000)
    except TypeError:                     # fakes/older providers without max_results
        ids = provider.list_inbox(query)
    with conn.cursor() as cur:
        known = {r[0] for r in cur.execute(
            "select provider_message_id from replies where mailbox = %s and provider_message_id = any(%s)",
            (mailbox, ids),
        )}
    counts: dict[str, int] = {}
    for message_id in ids:
        if message_id in known:
            continue
        inbound = provider.get_message(message_id)   # a fetch error fails the sync: the tick then doesn't send from this mailbox
        if inbound["from_email"] == mailbox.lower():
            continue
        try:
            result = record_inbound(conn, mailbox, inbound)
        except Exception as exc:  # noqa: BLE001 - one unreadable message must not block the mailbox forever
            _park_unreadable(conn, mailbox, inbound, exc)
            result = {"category": "unreadable (for a human)"}
        counts[result["category"]] = counts.get(result["category"], 0) + 1
    return counts


def _park_unreadable(conn, mailbox: str, inbound: dict, exc: Exception) -> None:
    """Stores a message we couldn't process as a needs-human reply, so it's
    seen by a person and not retried (and crashing) every tick."""
    with conn.transaction():
        conn.execute(
            "insert into replies (from_email, subject, body, provider_message_id, mailbox, category, needs_human, received_at) "
            "values (%s, %s, %s, %s, %s, 'unknown', true, now()) on conflict do nothing",
            (str(inbound.get("from_email") or "")[:320], str(inbound.get("subject") or "")[:500].replace("\x00", ""),
             f"(Velarqo couldn't process this message automatically: {type(exc).__name__}. Read it in the mailbox.)",
             inbound.get("provider_message_id"), mailbox),
        )
    note_problem(conn, mailbox, f"could not process message {inbound.get('provider_message_id')}: {type(exc).__name__}: {exc}"[:500])


# --- Stop rules and status ----------------------------------------------

def check_stop_rules(conn) -> str | None:
    with conn.cursor() as cur:
        sent, bounced = cur.execute(
            "select count(*), count(bounced_at) from messages where status = 'sent' and sent_at >= now() - interval '7 days'"
        ).fetchone()
    if guards.bounce_stop(sent, bounced) and controls(conn)["sending_enabled"]:
        reason = f"bounce rate {bounced}/{sent} over 7 days is above {guards.BOUNCE_STOP_RATE:.0%}"
        set_sending(conn, False, reason)
        return reason
    return None


def status(conn) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        campaigns = cur.execute(
            """
            select cp.id, cp.name, cp.status, cp.created_at,
                   count(*) filter (where m.status = 'queued') queued,
                   count(*) filter (where m.status = 'sent') sent,
                   count(m.bounced_at) bounced,
                   count(m.replied_at) replied,
                   count(*) filter (where m.status = 'skipped') skipped,
                   count(*) filter (where m.status = 'failed') failed,
                   count(*) filter (where m.status = 'sending') stuck_sending
            from campaigns cp left join messages m on m.campaign_id = cp.id
            group by cp.id order by cp.created_at
            """
        ).fetchall()
        today = cur.execute(
            "select mailbox, count(*) n from messages where status = 'sent' and sent_at >= %s group by mailbox",
            (guards.uk_day_start(_now()),),
        ).fetchall()
        inbox = cur.execute(
            "select count(*) filter (where needs_human and handled_at is null) needs_human, count(*) total from replies"
        ).fetchone()
    return {"controls": controls(conn), "campaigns": campaigns, "sent_today": today, "replies": inbox}


def open_replies(conn) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            select r.id, r.received_at, r.from_email, r.category, r.subject, r.body, c.display_name, c.phone, c.website
            from replies r left join companies c on c.id = r.company_id
            where r.needs_human and r.handled_at is null
            order by r.received_at
            """
        ).fetchall()


def mark_handled(conn, reply_id: str, human_category: str | None = None) -> None:
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            "update replies set handled_at = now(), human_category = coalesce(%s, human_category) where id = %s",
            (human_category, reply_id),
        )


# --- Funnel outcomes and experiment results -----------------------------

FUNNEL_STAGES = ("call_booked", "call_held", "sample_received", "pilot_signed", "lost")


def find_company(conn, ref: str) -> dict | None:
    """By company id, email address, or @domain."""
    with conn.cursor(row_factory=dict_row) as cur:
        if "@" not in ref:
            return cur.execute("select * from companies where id::text = %s", (ref,)).fetchone()
        if ref.startswith("@"):
            return cur.execute(
                "select * from companies where lower(split_part(email, '@', 2)) = lower(%s) limit 1", (ref[1:],)
            ).fetchone()
        return cur.execute(
            """
            select c.* from companies c
            where lower(c.email) = lower(%s)
               or exists (select 1 from messages m where m.company_id = c.id and lower(m.to_email) = lower(%s))
               or exists (select 1 from replies r where r.company_id = c.id and lower(r.from_email) = lower(%s))
            limit 1
            """, (ref, ref, ref),
        ).fetchone()


def log_outcome(conn, company_id, stage: str, payload: dict) -> None:
    if stage not in FUNNEL_STAGES:
        raise ValueError(f"stage must be one of {FUNNEL_STAGES}")
    with conn.transaction(), conn.cursor() as cur:
        _event(cur, stage, company_id, payload=payload)


def company_history(conn, company_id) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        return {
            "messages": cur.execute(
                "select sequence_step, status, sent_at, subject, variant_index from messages "
                "where company_id = %s order by sequence_step", (company_id,)).fetchall(),
            "replies": cur.execute(
                "select received_at, coalesce(human_category, category) category, body from replies "
                "where company_id = %s order by received_at", (company_id,)).fetchall(),
            "events": cur.execute(
                "select occurred_at, type, payload from events where company_id = %s and type = any(%s) "
                "order by occurred_at", (company_id, list(FUNNEL_STAGES))).fetchall(),
        }


def cold_email_results(conn, experiment_name: str) -> list[dict]:
    """Per arm, counted per company: sent -> replied -> positive -> call -> sample -> pilot."""
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            with assigned as (
              select m.company_id, m.variant_index, m.bounced_at
              from messages m join campaigns cp on cp.id = m.campaign_id
              where m.sequence_step = 1 and m.status = 'sent' and cp.settings->'experiment'->>'name' = %s
            ),
            r as (
              select company_id, array_agg(coalesce(human_category, category)) cats
              from replies where company_id is not null group by company_id
            ),
            e as (select company_id, array_agg(type) types from events where type = any(%s) group by company_id)
            select a.variant_index,
                   count(*) sent,
                   count(a.bounced_at) bounced,
                   count(*) filter (where r.cats && array['positive','unknown','not_interested','unsubscribe','complaint']) replied,
                   count(*) filter (where 'positive' = any(r.cats)) positive,
                   count(*) filter (where r.cats && array['unsubscribe','complaint']) opted_out,
                   count(*) filter (where 'complaint' = any(r.cats)) complaints,
                   count(*) filter (where e.types && array['call_booked','call_held']) calls,
                   count(*) filter (where 'sample_received' = any(e.types)) samples,
                   count(*) filter (where 'pilot_signed' = any(e.types)) pilots
            from assigned a
            left join r on r.company_id = a.company_id
            left join e on e.company_id = a.company_id
            group by a.variant_index order by a.variant_index
            """, (experiment_name, list(FUNNEL_STAGES)),
        ).fetchall()


def pricing_results(conn, experiment_name: str) -> list[dict]:
    """Per price arm, counted per company that had a call where the price was quoted."""
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            with quoted as (
              select distinct on (company_id) company_id, payload->>'price_arm' arm, payload->>'price_reaction' reaction
              from events where type = 'call_held' and payload->>'pricing_experiment' = %s
              order by company_id, occurred_at desc
            )
            select q.arm, count(*) calls,
                   count(*) filter (where q.reaction = 'objected') price_objections,
                   count(*) filter (where exists (select 1 from events x where x.company_id = q.company_id
                                                   and x.type = 'sample_received')) samples,
                   count(*) filter (where exists (select 1 from events x where x.company_id = q.company_id
                                                   and x.type = 'pilot_signed')) pilots
            from quoted q group by q.arm order by q.arm
            """, (experiment_name,),
        ).fetchall()


def dry_run(conn, fn, *args, **kwargs):
    """Run fn inside a transaction that is always rolled back."""
    result = None
    with conn.transaction():
        result = fn(*args, **kwargs)
        raise psycopg.Rollback()
    return result
