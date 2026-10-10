"""Where an alert goes: Pablo's phone (ntfy.sh topic or a Telegram bot) and
his Gmail (sent from one of the sending mailboxes). All free, all set up
through .env, nothing in code:

    VELARQO_ALERT_EMAIL      where the email copy goes (e.g. your Gmail)
    VELARQO_ALERT_MAILBOX    which configured mailbox sends it (default: the first enabled one)
    NTFY_TOPIC               ntfy.sh topic name (install the ntfy app, subscribe to the same topic)
    NTFY_SERVER              optional, default https://ntfy.sh
    TELEGRAM_BOT_TOKEN       from @BotFather
    TELEGRAM_CHAT_ID         your chat id (message the bot once, then read getUpdates)

Set them with `python scripts/set_secret.py NAME`. A topic name is a
password: anyone who knows it can read the alerts, so make it long.

A channel that is not configured is skipped. A channel that fails never
stops the others: the result lists what worked and what did not.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).parents[2] / ".env"
NTFY_DEFAULT = "https://ntfy.sh"
TELEGRAM_API = "https://api.telegram.org"
# ntfy priorities: 5 max (phone buzzes through do-not-disturb), 4 high, 3 default, 2 low, 1 min
PRIORITY = {"urgent": 5, "high": 4, "normal": 3, "low": 2}


def settings() -> dict:
    load_dotenv(ENV_PATH)
    return {
        "email_to": os.environ.get("VELARQO_ALERT_EMAIL") or None,
        "mailbox": os.environ.get("VELARQO_ALERT_MAILBOX") or None,
        "ntfy_topic": os.environ.get("NTFY_TOPIC") or None,
        "ntfy_server": (os.environ.get("NTFY_SERVER") or NTFY_DEFAULT).rstrip("/"),
        "telegram_token": os.environ.get("TELEGRAM_BOT_TOKEN") or None,
        "telegram_chat": os.environ.get("TELEGRAM_CHAT_ID") or None,
    }


@dataclass
class Alert:
    title: str
    body: str                       # plain text; the push shows the first lines, the email shows all of it
    priority: str = "normal"        # urgent / high / normal / low
    tags: list[str] = field(default_factory=list)


@dataclass
class Delivery:
    channel: str
    ok: bool
    detail: str = ""


class Notifier:
    """Sends one Alert to every configured channel.

    `send_email(to, subject, body)` is injected (a mailbox provider's
    send_email, or a fake in tests); `session` is a requests.Session (a
    fake in tests). Nothing here touches the database."""

    def __init__(self, config: dict | None = None, send_email=None, session=None, timeout: int = 15):
        self.config = config if config is not None else settings()
        self.send_email = send_email
        self.session = session or requests.Session()
        self.timeout = timeout

    @property
    def channels(self) -> list[str]:
        c = self.config
        out = []
        if c.get("ntfy_topic"):
            out.append("ntfy")
        if c.get("telegram_token") and c.get("telegram_chat"):
            out.append("telegram")
        if c.get("email_to") and self.send_email:
            out.append("email")
        return out

    def send(self, alert: Alert, push: bool = True, email: bool = True) -> list[Delivery]:
        results = []
        for channel in self.channels:
            if (channel == "email" and not email) or (channel != "email" and not push):
                continue
            try:
                getattr(self, f"_{channel}")(alert)
                results.append(Delivery(channel, True))
            except Exception as exc:  # noqa: BLE001 - one dead channel must not lose the others
                results.append(Delivery(channel, False, f"{type(exc).__name__}: {str(exc)[:200]}"))
        return results

    def _ntfy(self, alert: Alert) -> None:
        # Headers must be latin-1: the title is forced to ASCII, the body (UTF-8) goes in the request body.
        headers = {
            "Title": alert.title.encode("ascii", "replace").decode(),
            "Priority": str(PRIORITY.get(alert.priority, 3)),
            "Tags": ",".join(alert.tags) if alert.tags else "email",
        }
        response = self.session.post(f"{self.config['ntfy_server']}/{self.config['ntfy_topic']}",
                                     data=alert.body.encode("utf-8"), headers=headers, timeout=self.timeout)
        response.raise_for_status()

    def _telegram(self, alert: Alert) -> None:
        text = f"{alert.title}\n\n{alert.body}"[:4000]   # Telegram's message limit is 4096 characters
        response = self.session.post(
            f"{TELEGRAM_API}/bot{self.config['telegram_token']}/sendMessage",
            json={"chat_id": self.config["telegram_chat"], "text": text, "disable_web_page_preview": True},
            timeout=self.timeout,
        )
        response.raise_for_status()

    def _email(self, alert: Alert) -> None:
        self.send_email(to=self.config["email_to"], subject=alert.title, body=alert.body)
