"""Parse weight entries from life-os health-log.md."""

import re
from datetime import date, datetime
from pathlib import Path


def parse_health_log(path: str | Path) -> list[dict]:
    """Parse health-log.md and return weight entries sorted by date.

    Returns list of dicts: [{"date": date, "weight": float}, ...]
    Entries without a weight field are skipped.
    """
    text = Path(path).read_text(encoding="utf-8")

    entries = []
    current_date = None

    date_pattern = re.compile(r"^## (\d{4}-\d{2}-\d{2})")
    weight_pattern = re.compile(r"^- \*\*Weight:\*\*\s*([\d.]+)")

    for line in text.splitlines():
        date_match = date_pattern.match(line)
        if date_match:
            current_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()
            continue

        if current_date is None:
            continue

        weight_match = weight_pattern.match(line)
        if weight_match:
            entries.append({
                "date": current_date,
                "weight": float(weight_match.group(1)),
            })
            current_date = None  # Move on, one weight per date section

    entries.sort(key=lambda e: e["date"])
    return entries


def entries_to_json_serializable(entries: list[dict]) -> list[dict]:
    """Convert entries to JSON-safe format (date -> ISO string)."""
    return [
        {"date": e["date"].isoformat(), "weight": e["weight"]}
        for e in entries
    ]
