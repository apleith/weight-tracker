"""Check for missing health log entry and send push notification via ntfy.sh."""

import re
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen


def today_is_logged(health_log_path: str | Path) -> bool:
    """Check if today's date has an entry in health-log.md."""
    text = Path(health_log_path).read_text(encoding="utf-8")
    today_header = f"## {date.today().isoformat()}"
    return today_header in text


def send_ntfy(topic: str, title: str, message: str, priority: str = "default", tags: str = ""):
    """Send a push notification via ntfy.sh."""
    headers = {
        "Title": title,
        "Priority": priority,
    }
    if tags:
        headers["Tags"] = tags

    req = Request(
        f"https://ntfy.sh/{topic}",
        data=message.encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urlopen(req) as resp:
        return resp.status


def remind_if_missing(config: dict) -> bool:
    """Check health log and send reminder if today is missing.

    Returns True if a notification was sent, False if already logged.
    """
    ntfy = config.get("ntfy", {})
    topic = ntfy.get("topic")
    if not topic:
        print("[remind] No ntfy topic configured in config.yaml")
        return False

    if today_is_logged(config["health_log_path"]):
        print(f"[remind] {date.today().isoformat()} already logged. No reminder sent.")
        return False

    send_ntfy(
        topic=topic,
        title="Health Log Reminder",
        message="You haven't logged your health today. Weight, meds, sleep, mood, moved.",
        priority=ntfy.get("priority", "default"),
        tags="memo,health",
    )
    print(f"[remind] Reminder sent for {date.today().isoformat()}")
    return True
