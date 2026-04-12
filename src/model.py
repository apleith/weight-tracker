"""Piecewise linear weight projection model.

Calibrated to TDEE dynamics, SURMOUNT plateau timing, metabolic adaptation,
and keto + tirzepatide combination. Breakpoints should be recalibrated monthly
as real data accumulates.
"""

from datetime import date

START_DATE = date(2026, 3, 16)
START_WEIGHT = 660.0
GOAL_WEIGHT = 245.0

# Default breakpoints: (day, weight)
DEFAULT_BREAKPOINTS = [
    (0, 660),
    (14, 640),
    (28, 620),
    (168, 525),
    (364, 418),
    (525, 375),
]


def expected_weight(day: int, breakpoints: list[tuple[int, float]] | None = None) -> float:
    """Return expected weight in lbs for a given day number.

    day = days since START_DATE (March 16, 2026).
    """
    bp = breakpoints or DEFAULT_BREAKPOINTS

    if day <= bp[0][0]:
        return bp[0][1]

    for i in range(1, len(bp)):
        if day <= bp[i][0]:
            d0, w0 = bp[i - 1]
            d1, w1 = bp[i]
            fraction = (day - d0) / (d1 - d0)
            return w0 + fraction * (w1 - w0)

    return bp[-1][1]


def day_number(d: date) -> int:
    """Convert a date to day number since start."""
    return (d - START_DATE).days


def expected_weight_on(d: date, breakpoints=None) -> float:
    """Expected weight for a calendar date."""
    return expected_weight(day_number(d), breakpoints)


def compute_stats(entries: list[dict], breakpoints=None) -> dict:
    """Compute dashboard statistics from weight entries.

    entries: list of {"date": date, "weight": float}
    Returns dict with all KPIs needed by dashboard surfaces.
    """
    if not entries:
        return {
            "current_weight": START_WEIGHT,
            "start_weight": START_WEIGHT,
            "goal_weight": GOAL_WEIGHT,
            "total_lost": 0,
            "pct_lost": 0,
            "day_number": 0,
            "days_remaining": 525,
            "expected_today": START_WEIGHT,
            "deviation": 0,
            "avg_weekly_rate": 0,
            "latest_date": START_DATE.isoformat(),
            "on_track": True,
        }

    latest = entries[-1]
    current = latest["weight"]
    today_day = day_number(latest["date"])
    exp_today = expected_weight(today_day, breakpoints)
    total_lost = START_WEIGHT - current

    # Weekly rate: total lost / weeks elapsed (avoid division by zero)
    weeks = max(today_day / 7, 1)
    avg_weekly = total_lost / weeks

    # 7-day rate if enough data
    recent = [e for e in entries if (latest["date"] - e["date"]).days <= 7]
    if len(recent) >= 2:
        week_loss = recent[0]["weight"] - recent[-1]["weight"]
        weekly_rate = week_loss  # Already 7-day window
    else:
        weekly_rate = avg_weekly

    return {
        "current_weight": current,
        "start_weight": START_WEIGHT,
        "goal_weight": GOAL_WEIGHT,
        "total_lost": round(total_lost, 1),
        "pct_lost": round((total_lost / START_WEIGHT) * 100, 1),
        "day_number": today_day,
        "days_remaining": max(525 - today_day, 0),
        "expected_today": round(exp_today, 1),
        "deviation": round(current - exp_today, 1),  # negative = ahead of schedule
        "avg_weekly_rate": round(avg_weekly, 1),
        "recent_weekly_rate": round(weekly_rate, 1),
        "latest_date": latest["date"].isoformat(),
        "on_track": current <= exp_today,
    }


def generate_curve(breakpoints=None, total_days: int = 525) -> list[dict]:
    """Generate the full expected weight curve for charting.

    Returns list of {"day": int, "weight": float} for each day 0..total_days.
    """
    return [
        {"day": d, "weight": round(expected_weight(d, breakpoints), 1)}
        for d in range(total_days + 1)
    ]
