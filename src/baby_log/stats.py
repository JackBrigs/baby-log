"""Statistics calculation and formatting."""

from datetime import datetime
from typing import Any

from baby_log.events import EventType, sheet_row_to_event_type


def _parse_ts(s: str) -> datetime | None:
    """Parse DD.MM.YYYY HH:MM timestamp."""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%d.%m.%Y %H:%M")
    except (ValueError, TypeError):
        return None


def _fmt(s: str) -> str:
    """Extract HH:MM from DD.MM.YYYY HH:MM string."""
    if not s:
        return "--:--"
    try:
        return s[-5:]
    except (IndexError, AttributeError):
        return "--:--"


def _parse_duration(start_str: str, end_str: str) -> int | None:
    """Parse two timestamps and return duration in seconds."""
    start = _parse_ts(start_str)
    end = _parse_ts(end_str)
    if start is None or end is None:
        return None
    delta = (end - start).total_seconds()
    return int(delta) if delta >= 0 else None


def _get_type(ev: dict[str, Any]) -> EventType | None:
    """Get EventType from event dict (new Russian label or legacy English)."""
    label = ev.get("Тип", ev.get("event_type", ""))
    return sheet_row_to_event_type(label)


def calculate_daily_stats(events: list[dict[str, Any]]) -> str:
    """Calculate and format statistics for a single day."""
    intervals: list[dict[str, Any]] = []
    started: list[dict[str, Any]] = []
    ended: list[dict[str, Any]] = []
    feedings: list[dict[str, Any]] = []
    walks: list[dict[str, Any]] = []

    for ev in events:
        etype = _get_type(ev)
        if etype == EventType.SLEEP:
            if ev.get("Детали"):
                intervals.append(ev)
            else:
                started.append(ev)
        elif etype == EventType.FEEDING:
            feedings.append(ev)
        elif etype == EventType.WALK:
            if ev.get("Детали"):
                walks.append(ev)
            else:
                started.append(ev)

    if not intervals and not started and not ended and not feedings and not walks:
        return "  Нет событий за этот день."

    lines: list[str] = []
    total_sleep = 0

    # Sleep intervals
    for ev in intervals:
        ts = ev.get("Время", "")
        detail = ev.get("Детали", "")
        if detail.startswith("до "):
            end_str = detail[3:]
            dur = _parse_duration(ts, end_str)
        else:
            dur = None
        if dur is not None:
            total_sleep += dur
            lines.append(f"  Сон: {_fmt(ts)} – {_fmt(detail)}")

    # Feeding events
    lines.append(f"  Кормлений: {len(feedings)}")
    for ev in feedings:
        lines.append(f"    {_fmt(ev.get('Время', ''))}")

    # Walks
    if walks:
        lines.append(f"  Прогулок: {len(walks)}")

    hours = total_sleep // 3600
    minutes = (total_sleep % 3600) // 60
    lines.append(f"\n  Всего сна: {hours}ч {minutes}мин")

    return "\n".join(lines)


def calculate_weekly_stats(events: list[dict[str, Any]]) -> str:
    """Calculate and format statistics for a multi-day range."""
    by_day: dict[str, list[dict[str, Any]]] = {}
    for ev in events:
        ts = ev.get("Время", ev.get("timestamp", ""))
        # Extract date from DD.MM.YYYY HH:MM
        if " " in ts:
            day_key = ts.split(" ")[0]
        else:
            day_key = ts[:10] if ts else "unknown"
        by_day.setdefault(day_key, []).append(ev)

    if not by_day:
        return "Нет событий за выбранный период."

    lines: list[str] = []
    total_seconds = 0
    total_feedings = 0

    for day_key in sorted(by_day.keys()):
        day_events = by_day[day_key]
        lines.append(f"📅 {day_key}")

        day_sleep = 0
        day_feedings = 0

        for ev in day_events:
            etype = _get_type(ev)
            if etype == EventType.SLEEP:
                ts = ev.get("Время", "")
                detail = ev.get("Детали", "")
                if detail and detail.startswith("до "):
                    end_str = detail[3:]
                    dur = _parse_duration(ts, end_str)
                    if dur:
                        day_sleep += dur
                        lines.append(f"  Сон: {_fmt(ts)} – {_fmt(detail)}")
            elif etype == EventType.FEEDING:
                day_feedings += 1
                lines.append(f"  Кормление: {_fmt(ev.get('Время', ''))}")

        hours = day_sleep // 3600
        minutes = (day_sleep % 3600) // 60
        lines.append(f"  Итого: {hours}ч {minutes}мин сна, {day_feedings} кормл.")
        lines.append("")

        total_seconds += day_sleep
        total_feedings += day_feedings

    total_h = total_seconds // 3600
    total_m = (total_seconds % 3600) // 60
    lines.append(f"📊 За период: {total_h}ч {total_m}мин сна, {total_feedings} кормлений.")

    return "\n".join(lines)
