import click

from data.db import get_connection, init_db
from lib.tracking.insights import (
    overall_summary,
    segment_effectiveness,
    send_time_performance,
    variant_performance,
)


def print_report() -> None:
    init_db()
    conn = get_connection()
    try:
        summary = overall_summary(conn)
        click.echo("=== Overall ===")
        click.echo(f"Sent: {summary['sent']}")
        click.echo(f"Reply rate: {summary['reply_rate']:.1%}")
        click.echo(f"Appointment rate: {summary['appointment_rate']:.1%}")
        click.echo(f"Close rate: {summary['close_rate']:.1%}")
        click.echo(f"Revenue: {summary['revenue']:.2f}")
        click.echo(f"Revenue per 100 leads: {summary['revenue_per_100_leads']:.2f}\n")

        click.echo("=== By message variant ===")
        for row in variant_performance(conn):
            click.echo(
                f"  variant {row['message_variant']}: sent={row['sent']:4} "
                f"reply={row['reply_rate']:.1%} appt={row['appointment_rate']:.1%} "
                f"close={row['close_rate']:.1%} revenue/send={row['revenue_per_send']:.2f}"
            )

        click.echo("\n=== By segment ===")
        for row in segment_effectiveness(conn):
            click.echo(
                f"  {row['segment']:10}: sent={row['sent']:4} "
                f"reply={row['reply_rate']:.1%} close={row['close_rate']:.1%} "
                f"revenue/100={row['revenue_per_100']:.2f}"
            )

        click.echo("\n=== By send day ===")
        for row in send_time_performance(conn):
            click.echo(f"  {row['send_day']:10}: sent={row['sent']:4} reply={row['reply_rate']:.1%}")
    finally:
        conn.close()


@click.command()
def main() -> None:
    print_report()


if __name__ == "__main__":
    main()
