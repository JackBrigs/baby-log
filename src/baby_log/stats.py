"""Statistics calculation and formatting."""

from datetime import datetime
from typing import Any

from baby_log.events import EVENT_LABELS, EventType, sheet_row_to_event_type


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


def _format_duration(seconds: int) -> str:
    """Format seconds as human-readable duration string."""
    if seconds == 0:
        return "0мин"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    parts = []
    if hours:
        parts.append(f"{hours}ч")
    if minutes:
        parts.append(f"{minutes}мин")
    return " ".join(parts)


def _get(ev: dict[str, Any], *keys: str) -> str:
    """Get a value from an event dict, trying multiple key names (case-insensitive)."""
    # First try exact matches
    for key in keys:
        val = ev.get(key)
        if val:
            return str(val)
    # Fall back to case-insensitive search
    lower_map = {k.lower(): v for k, v in ev.items()}
    for key in keys:
        val = lower_map.get(key.lower())
        if val:
            return str(val)
    return ""


def _get_type(ev: dict[str, Any]) -> EventType | None:
    """Get EventType from event dict."""
    label = _get(ev, "Тип активности", "Тип")
    return sheet_row_to_event_type(label)


def _extract_start(ev: dict[str, Any]) -> str:
    """Extract start time from an event dict."""
    return _get(ev, "Дата и время начала", "Дата начала", "Начало", "Время")


def _extract_end(ev: dict[str, Any]) -> str:
    """Extract end time from an event dict, or empty string if incomplete."""
    end = _get(ev, "дата и время окончания", "Время окончания", "Окончание", "Детали")
    if end.startswith("до "):
        end = end[3:]
    return end


def _is_completed(ev: dict[str, Any]) -> bool:
    """Return True if the event has both start and end times."""
    return bool(_extract_start(ev)) and bool(_extract_end(ev))


def calculate_daily_stats(events: list[dict[str, Any]]) -> str:
    """Calculate and format statistics for a single day."""
    # Group events by type — store both completed intervals and incomplete starts
    type_completed: dict[EventType, list[dict[str, Any]]] = {
        EventType.SLEEP: [],
        EventType.FEEDING: [],
        EventType.WALK: [],
    }
    type_started: dict[EventType, list[dict[str, Any]]] = {
        EventType.SLEEP: [],
        EventType.FEEDING: [],
        EventType.WALK: [],
    }

    for ev in events:
        etype = _get_type(ev)
        if etype is None:
            continue
        if _is_completed(ev):
            type_completed[etype].append(ev)
        else:
            type_started[etype].append(ev)

    # Check if there's anything to show
    if not any(type_completed.values()) and not any(type_started.values()):
        return "  Нет событий за этот день."

    lines: list[str] = []

    for etype in (EventType.SLEEP, EventType.FEEDING, EventType.WALK):
        completed = type_completed[etype]
        started = type_started[etype]
        if not completed and not started:
            continue

        label = EVENT_LABELS[etype]
        lines.append(f"{label}")

        total_seconds = 0
        idx = 1

        # Completed intervals
        for ev in completed:
            start = _extract_start(ev)
            end = _extract_end(ev)
            lines.append(f"{idx}. {_fmt(start)} – {_fmt(end)}")
            dur = _parse_duration(start, end)
            if dur:
                total_seconds += dur
            idx += 1

        # Incomplete (started but not ended)
        for ev in started:
            start = _extract_start(ev)
            lines.append(f"{idx}. {_fmt(start)} (начался)")
            idx += 1

        if completed:
            lines.append(f"Общее время: {_format_duration(total_seconds)}")
        lines.append("")

    return "\n".join(lines).rstrip()


def calculate_weekly_stats(events: list[dict[str, Any]]) -> str:
    """Calculate and format statistics for a multi-day range."""
    # Group events by date
    by_day: dict[str, list[dict[str, Any]]] = {}
    for ev in events:
        start = _extract_start(ev)
        if " " in start:
            day_key = start.split(" ")[0]
        elif start:
            day_key = start[:10]
        else:
            day_key = "unknown"
        by_day.setdefault(day_key, []).append(ev)

    if not by_day:
        return "Нет событий за выбранный период."

    lines: list[str] = []
    grand_total_sleep = 0
    grand_total_feeding = 0
    grand_total_walk = 0

    for day_key in sorted(by_day.keys()):
        day_events = by_day[day_key]
        lines.append(f"📅 {day_key}")

        # Group events by type for this day
        type_completed: dict[EventType, list[dict[str, Any]]] = {
            EventType.SLEEP: [],
            EventType.FEEDING: [],
            EventType.WALK: [],
        }
        type_started: dict[EventType, list[dict[str, Any]]] = {
            EventType.SLEEP: [],
            EventType.FEEDING: [],
            EventType.WALK: [],
        }

        for ev in day_events:
            etype = _get_type(ev)
            if etype is None:
                continue
            if _is_completed(ev):
                type_completed[etype].append(ev)
            else:
                type_started[etype].append(ev)

        day_has_data = False
        for etype in (EventType.SLEEP, EventType.FEEDING, EventType.WALK):
            completed = type_completed[etype]
            started = type_started[etype]
            if not completed and not started:
                continue

            day_has_data = True
            label = EVENT_LABELS[etype]
            lines.append(f"  {label}")

            total_seconds = 0
            idx = 1

            # Completed intervals
            for ev in completed:
                start = _extract_start(ev)
                end = _extract_end(ev)
                lines.append(f"    {idx}. {_fmt(start)} – {_fmt(end)}")
                dur = _parse_duration(start, end)
                if dur:
                    total_seconds += dur
                idx += 1

            # Incomplete (started but not ended)
            for ev in started:
                start = _extract_start(ev)
                lines.append(f"    {idx}. {_fmt(start)} (начался)")
                idx += 1

            if completed:
                lines.append(f"    Общее время: {_format_duration(total_seconds)}")
            lines.append("")

            if etype == EventType.SLEEP:
                grand_total_sleep += total_seconds
            elif etype == EventType.FEEDING:
                grand_total_feeding += total_seconds
            elif etype == EventType.WALK:
                grand_total_walk += total_seconds

        if not day_has_data:
            lines.append("  Нет событий")
            lines.append("")

    # Summary
    lines.append("📊 Итого за период:")
    if grand_total_sleep:
        lines.append(f"  Сон: {_format_duration(grand_total_sleep)}")
    if grand_total_feeding:
        lines.append(f"  Кормление: {_format_duration(grand_total_feeding)}")
    if grand_total_walk:
        lines.append(f"  Прогулка: {_format_duration(grand_total_walk)}")

    return "\n".join(lines)
