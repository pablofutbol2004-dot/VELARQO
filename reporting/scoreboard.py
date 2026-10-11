"""The daily scoreboard line from docs/PATH_6_MONTHS.md section 6:
sent / bounces / replies / positive / calls / samples / pilots, today and
cumulative, per cold-email arm and per sequence step.

    python -m pipelines.outbound scoreboard            # print
    python -m pipelines.outbound scoreboard --csv      # also write data/scoreboard_<day>.csv
    python -m pipelines.outbound scoreboard --notify   # also push/email it (once per day)
    python -m reporting.scoreboard                     # same, standalone

"Today" is the UK calendar day. Replies count people only (no bounces,
no auto-replies); positive uses the human's correction when there is one.
Calls, samples and pilots are the funnel events logged with `outcome`,
counted once per company, attributed to the arm of its first email.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path

import click
from psycopg.rows import dict_row

from outreach.send_engine import guards

ROOT = Path(__file__).parents[1]
METRICS = ("sent", "bounces", "replies", "positive", "calls", "samples", "pilots", "opt_outs")
HUMAN_CATEGORIES = ("positive", "unknown", "not_interested", "unsubscribe", "complaint")


def _now() -> datetime:
    return datetime.now(timezone.utc)


_METRIC_SQL = """
    select {key}
           count(distinct m.id) filter (where m.status = 'sent' and m.sent_at >= %(since)s) sent_today,
           count(distinct m.id) filter (where m.status = 'sent') sent_total,
           count(distinct m.id) filter (where m.bounced_at >= %(since)s) bounces_today,
           count(distinct m.id) filter (where m.bounced_at is not null) bounces_total,
           count(distinct r.id) filter (where r.cat = any(%(human)s) and r.received_at >= %(since)s) replies_today,
           count(distinct r.id) filter (where r.cat = any(%(human)s)) replies_total,
           count(distinct r.id) filter (where r.cat = 'positive' and r.received_at >= %(since)s) positive_today,
           count(distinct r.id) filter (where r.cat = 'positive') positive_total,
           count(distinct r.id) filter (where r.cat in ('unsubscribe', 'complaint') and r.received_at >= %(since)s) opt_outs_today,
           count(distinct r.id) filter (where r.cat in ('unsubscribe', 'complaint')) opt_outs_total
    from messages m
    join campaigns cp on cp.id = m.campaign_id
    left join (select id, message_id, received_at, coalesce(human_category, category) cat from replies) r
           on r.message_id = m.id
    {where}
    group by {group} order by {group}
"""

_FUNNEL_SQL = """
    with assigned as (
      select distinct on (m.company_id) m.company_id, m.sequence_step,
             cp.settings->'experiment'->>'name' experiment,
             coalesce(cp.settings->'experiment'->'arms'->m.variant_index->>'key', 'arm ' || m.variant_index::text) arm
      from messages m join campaigns cp on cp.id = m.campaign_id
      where m.status = 'sent' order by m.company_id, m.sequence_step
    ),
    firsts as (
      select company_id, type, min(occurred_at) at from events
      where type in ('call_booked', 'call_held', 'sample_received', 'pilot_signed') group by company_id, type
    )
    select {key}
           count(distinct f.company_id) filter (where f.type in ('call_booked', 'call_held') and f.at >= %(since)s) calls_today,
           count(distinct f.company_id) filter (where f.type in ('call_booked', 'call_held')) calls_total,
           count(distinct f.company_id) filter (where f.type = 'sample_received' and f.at >= %(since)s) samples_today,
           count(distinct f.company_id) filter (where f.type = 'sample_received') samples_total,
           count(distinct f.company_id) filter (where f.type = 'pilot_signed' and f.at >= %(since)s) pilots_today,
           count(distinct f.company_id) filter (where f.type = 'pilot_signed') pilots_total
    from firsts f left join assigned a on a.company_id = f.company_id
    group by {group} order by {group}
"""


def _rows(cur, sql: str, params: dict) -> list[dict]:
    return cur.execute(sql, params).fetchall()


def _merge(metric_rows: list[dict], funnel_rows: list[dict], keys: tuple[str, ...]) -> list[dict]:
    """One row per key with today/total for every metric (zeros where a side has nothing)."""
    out: dict[tuple, dict] = {}
    for row in metric_rows + funnel_rows:
        k = tuple(row.get(key) for key in keys)
        entry = out.setdefault(k, {**{key: row.get(key) for key in keys},
                                   "today": dict.fromkeys(METRICS, 0), "total": dict.fromkeys(METRICS, 0)})
        for metric in METRICS:
            for period in ("today", "total"):
                value = row.get(f"{metric}_{period}")
                if value is not None:
                    entry[period][metric] = int(value)
    return [out[k] for k in sorted(out, key=lambda t: tuple(str(x) for x in t))]


def compute(conn, now: datetime | None = None) -> dict:
    now = now or _now()
    since = guards.uk_day_start(now)
    params = {"since": since, "human": list(HUMAN_CATEGORIES)}
    with conn.cursor(row_factory=dict_row) as cur:
        totals = _merge(
            _rows(cur, _METRIC_SQL.format(key="1 as k,", where="", group="1"), params),
            _rows(cur, _FUNNEL_SQL.format(key="1 as k,", group="1"), params), ("k",),
        )
        by_arm = _merge(
            _rows(cur, _METRIC_SQL.format(
                key="cp.settings->'experiment'->>'name' experiment, coalesce(cp.settings->'experiment'->'arms'->m.variant_index->>'key', 'arm ' || m.variant_index::text) arm,",
                where="", group="1, 2"), params),
            _rows(cur, _FUNNEL_SQL.format(key="a.experiment, a.arm,", group="1, 2"), params), ("experiment", "arm"),
        )
        by_step = _merge(
            _rows(cur, _METRIC_SQL.format(key="m.sequence_step step,", where="", group="1"), params),
            [], ("step",),
        )
        waiting = cur.execute(
            "select count(*) n, min(received_at) oldest from replies where needs_human and handled_at is null"
        ).fetchone()
        controls = cur.execute("select sending_enabled, paused_reason from send_controls").fetchone() or {}
        handled = cur.execute(
            "select count(*) n, avg(extract(epoch from handled_at - received_at)) / 60 minutes from replies "
            "where handled_at is not null and received_at >= %s", (since,),
        ).fetchone()
    empty = {"today": dict.fromkeys(METRICS, 0), "total": dict.fromkeys(METRICS, 0)}
    return {
        "day": since.date(),
        "today": (totals[0] if totals else empty)["today"],
        "total": (totals[0] if totals else empty)["total"],
        "by_arm": by_arm,
        "by_step": by_step,
        "waiting": int(waiting["n"]),
        "oldest_waiting_minutes": int((now - waiting["oldest"]).total_seconds() // 60) if waiting["oldest"] else None,
        "handled_today": int(handled["n"]),
        "minutes_to_handle": round(float(handled["minutes"]), 1) if handled["minutes"] is not None else None,
        "sending_enabled": bool(controls.get("sending_enabled")),
        "paused_reason": controls.get("paused_reason"),
    }


def _line(today: dict, total: dict, metrics=METRICS) -> str:
    return "  ".join(f"{m.replace('_', '-')} {today[m]}|{total[m]}" for m in metrics)


def format_text(board: dict, short: bool = False) -> str:
    """Plain text: the scoreboard line, then per arm and per step. `short`
    is for the phone (no step table)."""
    lines = [f"Velarqo scoreboard {board['day']:%a %d %b}  (today|total)",
             _line(board["today"], board["total"])]
    for row in board["by_arm"]:
        lines.append(f"  {row['experiment'] or '?'} / {row['arm']}: " + _line(row["today"], row["total"]))
    if not short:
        for row in board["by_step"]:
            lines.append(f"  step {row['step']}: " + _line(row["today"], row["total"], ("sent", "bounces", "replies", "positive", "opt_outs")))
    waiting = f"waiting for you: {board['waiting']}"
    if board["oldest_waiting_minutes"] is not None:
        waiting += f" (oldest {board['oldest_waiting_minutes'] // 60}h{board['oldest_waiting_minutes'] % 60:02d}m)"
    if board["minutes_to_handle"] is not None:
        waiting += f"; handled today {board['handled_today']}, avg {board['minutes_to_handle']:.0f} min to handle"
    lines.append(waiting)
    lines.append("sending: " + ("ON" if board["sending_enabled"] else f"OFF ({board['paused_reason'] or 'off'})"))
    return "\n".join(lines)


def write_csv(board: dict, out_dir: Path | None = None) -> Path:
    out_dir = out_dir or ROOT / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"scoreboard_{board['day']:%Y-%m-%d}.csv"
    fields = ["day", "scope", "experiment", "arm", "step", "period", *METRICS]
    rows = []
    for period in ("today", "total"):
        rows.append({"day": board["day"], "scope": "all", "period": period, **board[period]})
        for row in board["by_arm"]:
            rows.append({"day": board["day"], "scope": "arm", "experiment": row["experiment"], "arm": row["arm"],
                         "period": period, **row[period]})
        for row in board["by_step"]:
            rows.append({"day": board["day"], "scope": "step", "step": row["step"], "period": period, **row[period]})
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


@click.command("scoreboard")
@click.option("--csv", "to_csv", is_flag=True, help="Also write data/scoreboard_<day>.csv")
@click.option("--notify", is_flag=True, help="Also send it to the alert channels (once per day unless --force)")
@click.option("--force", is_flag=True, help="With --notify: send even if today's summary already went")
def scoreboard(to_csv, notify, force):
    """Today and cumulative: sent / bounces / replies / positive / calls / samples / pilots, per arm and per step."""
    from data.supabase_store import connect

    conn = connect()
    conn.autocommit = True
    board = compute(conn)
    click.echo(format_text(board))
    if to_csv:
        click.echo(f"written {write_csv(board)}")
    if notify:
        from outreach.alerts import replies as alerts
        from outreach.alerts.channels import Notifier

        result = alerts.send_daily_summary(conn, Notifier(send_email=alerts.email_sender()), board=board, force=force)
        click.echo(f"notify: {result}")


if __name__ == "__main__":
    scoreboard()
