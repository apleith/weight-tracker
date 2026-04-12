"""Recalibrate model breakpoints using actual weight data.

Uses least-squares linear regression on observed data to adjust future
breakpoints while preserving the piecewise phase structure. Requires at
least 14 days of data to be meaningful.
"""

from datetime import date
from .model import START_DATE, START_WEIGHT, GOAL_WEIGHT, DEFAULT_BREAKPOINTS, day_number


def recalibrate(entries: list[dict], current_breakpoints=None) -> dict:
    """Analyze actual data against model and propose updated breakpoints.

    Returns dict with analysis and proposed new breakpoints.
    """
    bp = list(current_breakpoints or DEFAULT_BREAKPOINTS)
    if not entries:
        return {"error": "No data to recalibrate from."}

    latest = entries[-1]
    latest_day = day_number(latest["date"])

    if latest_day < 14:
        return {"error": f"Only {latest_day} days of data. Wait until day 14+ for meaningful recalibration."}

    # Compute actual average daily loss rate
    total_lost = START_WEIGHT - latest["weight"]
    daily_rate = total_lost / latest_day

    # Compute rate per phase from actual data
    # Group entries by which breakpoint segment they fall in
    phase_data = []
    for i in range(1, len(bp)):
        d_start, _ = bp[i - 1]
        d_end, _ = bp[i]
        phase_entries = [e for e in entries if d_start < day_number(e["date"]) <= d_end]
        if len(phase_entries) >= 2:
            first, last = phase_entries[0], phase_entries[-1]
            days_span = day_number(last["date"]) - day_number(first["date"])
            if days_span > 0:
                rate = (first["weight"] - last["weight"]) / days_span
                phase_data.append({
                    "phase": i,
                    "days": f"{d_start}-{d_end}",
                    "entries": len(phase_entries),
                    "actual_daily_rate": round(rate, 2),
                })

    # Build proposed breakpoints by projecting from latest actual weight
    # For past breakpoints (already passed), use actual data
    # For future breakpoints, scale the original model's rate by the observed ratio
    proposed = [(0, START_WEIGHT)]

    # Find the model's predicted weight at latest_day using original breakpoints
    from .model import expected_weight
    model_at_latest = expected_weight(latest_day, bp)
    actual_at_latest = latest["weight"]

    # Ratio: if actual < model, we're losing faster than expected
    # Apply this ratio to scale future segment losses
    if model_at_latest > GOAL_WEIGHT:
        model_lost = START_WEIGHT - model_at_latest
        actual_lost = START_WEIGHT - actual_at_latest
        pace_ratio = actual_lost / model_lost if model_lost > 0 else 1.0
    else:
        pace_ratio = 1.0

    for i in range(1, len(bp)):
        bp_day, bp_weight = bp[i]
        if bp_day <= latest_day:
            # Past breakpoint: use nearest actual data or interpolate
            nearest = min(entries, key=lambda e: abs(day_number(e["date"]) - bp_day))
            proposed.append((bp_day, round(nearest["weight"], 1)))
        else:
            # Future breakpoint: project from latest actual weight
            days_ahead = bp_day - latest_day
            original_remaining_loss = bp_weight - model_at_latest
            adjusted_loss = original_remaining_loss * pace_ratio
            projected = actual_at_latest + adjusted_loss
            proposed.append((bp_day, round(max(projected, GOAL_WEIGHT), 1)))

    # Projected final weight
    final_bp = proposed[-1]
    projected_final = final_bp[1]

    # Estimated day to reach various milestones
    milestones = {}
    if daily_rate > 0:
        for target in [600, 500, 400, 300, GOAL_WEIGHT]:
            if actual_at_latest > target:
                days_needed = (actual_at_latest - target) / daily_rate
                milestone_day = latest_day + days_needed
                from datetime import timedelta
                milestone_date = START_DATE + timedelta(days=milestone_day)
                milestones[target] = {
                    "estimated_day": round(milestone_day),
                    "estimated_date": milestone_date.isoformat(),
                }

    return {
        "data_points": len(entries),
        "latest_day": latest_day,
        "latest_weight": actual_at_latest,
        "avg_daily_rate": round(daily_rate, 2),
        "avg_weekly_rate": round(daily_rate * 7, 1),
        "pace_ratio": round(pace_ratio, 2),
        "pace_description": (
            f"{'Ahead' if pace_ratio > 1 else 'Behind'} — "
            f"losing at {pace_ratio:.0%} of modeled rate"
        ),
        "phase_analysis": phase_data,
        "current_breakpoints": bp,
        "proposed_breakpoints": proposed,
        "projected_day525_weight": projected_final,
        "milestones": milestones,
    }


def format_report(result: dict) -> str:
    """Format recalibration results as a readable report."""
    if "error" in result:
        return f"[recalibrate] {result['error']}"

    lines = [
        "=" * 60,
        "MODEL RECALIBRATION REPORT",
        "=" * 60,
        f"Data points:     {result['data_points']}",
        f"Latest:          Day {result['latest_day']} — {result['latest_weight']} lbs",
        f"Avg daily loss:  {result['avg_daily_rate']} lbs/day",
        f"Avg weekly loss: {result['avg_weekly_rate']} lbs/week",
        f"Pace:            {result['pace_description']}",
        "",
        "PROPOSED BREAKPOINTS:",
        f"  {'Day':>5}  {'Current':>10}  {'Proposed':>10}  {'Diff':>8}",
        f"  {'-'*5}  {'-'*10}  {'-'*10}  {'-'*8}",
    ]

    for (cd, cw), (pd, pw) in zip(result["current_breakpoints"], result["proposed_breakpoints"]):
        diff = pw - cw
        lines.append(f"  {cd:>5}  {cw:>10.1f}  {pw:>10.1f}  {diff:>+8.1f}")

    lines.extend([
        "",
        f"Projected Day 525: {result['projected_day525_weight']} lbs",
        "",
        "MILESTONES (at current pace):",
    ])

    for target, info in result.get("milestones", {}).items():
        lines.append(f"  {target} lbs — Day {info['estimated_day']} ({info['estimated_date']})")

    lines.extend([
        "",
        "To apply proposed breakpoints, update model_breakpoints in config.yaml.",
        "=" * 60,
    ])

    return "\n".join(lines)
