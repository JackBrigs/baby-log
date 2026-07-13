"""Message parser for Russian baby-log commands."""

import re
from datetime import datetime

from baby_log.events import (
    EVENT_LABELS,
    CloseRequest,
    CompleteEvent,
    Event,
    EventType,
    HelpRequest,
    IncompleteEvent,
    IntervalEvent,
    ParseResult,
)

# ── Lexicon per event type ──────────────────────────────────

# (nominative, genitive, {start words}, {end words})
LEXICON = {
    EventType.SLEEP: ("сон", "сон", {"заснул", "сон"}, {"проснулся"}),
    EventType.FEEDING: ("еда", "еда", {"поел", "еда"}, {"наелся"}),
    EventType.WALK: ("прогулка", "прогулка", {"прогулка"}, {"вернулся"}),
}

# ── Compiled patterns ───────────────────────────────────────

_TIME = r"(\d{2}):(\d{2})"

PATTERNS: dict[EventType, dict[str, re.Pattern]] = {}

for _etype, (nom, gen, start_words, end_words) in LEXICON.items():
    sw = "|".join(start_words)
    ew = "|".join(end_words)
    PATTERNS[_etype] = {
        "standalone_start": re.compile(rf"^(?:{sw})\s*$", re.IGNORECASE),
        "standalone_end": re.compile(rf"^(?:{ew})\s*$", re.IGNORECASE),
        "from": re.compile(rf"^{gen}\s+с\s+{_TIME}\s*$", re.IGNORECASE),
        "from_to": re.compile(rf"^{gen}\s+с\s+{_TIME}\s+до\s+{_TIME}\s*$", re.IGNORECASE),
        "until": re.compile(
            rf"^{gen}\s+(?:до)\s+(?:в\s+)?{_TIME}\s*$",
            re.IGNORECASE,
        ),
        "ended_at": re.compile(rf"^{nom}\s+\w+\s+в\s+{_TIME}\s*$", re.IGNORECASE),
    }


# ── Helpers ─────────────────────────────────────────────────


class ParseError(Exception):
    """Raised when a message cannot be parsed into a valid event."""


def _parse_time(text: str) -> tuple[int, int]:
    """Parse HH:MM and validate."""
    m = re.match(r"^(\d{2}):(\d{2})$", text)
    if m is None:
        raise ParseError(f"Неверный формат времени: {text}. Ожидался ЧЧ:ММ.")
    hour, minute = int(m.group(1)), int(m.group(2))
    if hour > 23:
        raise ParseError(f"Неверный час: {hour}. Допустимо 00–23.")
    if minute > 59:
        raise ParseError(f"Неверная минута: {minute}. Допустимо 00–59.")
    return hour, minute


def _at_time(now: datetime, hour: int, minute: int) -> datetime:
    """Return a datetime on the same date as *now* at the given hour/minute."""
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def get_help_text() -> str:
    """Return user-facing help text in Russian."""
    return (
        "📋 Команды\n\n"
        "Регистр не важен.\n\n"
        "😴 Сон\n"
        "заснул\n"
        "сон с 12:30\n"
        "сон до 13:55\n"
        "сон с 12:30 до 13:55\n"
        "проснулся\n\n"
        "🍼 Кормление\n"
        "поел\n"
        "еда с 12:30\n"
        "еда до 13:55\n"
        "еда с 12:30 до 13:55\n"
        "наелся\n\n"
        "🚶 Прогулка\n"
        "прогулка\n"
        "прогулка с 12:30\n"
        "прогулка до 13:55\n"
        "прогулка с 12:30 до 13:55\n"
        "вернулся"
    )


# ── Main parser ─────────────────────────────────────────────


def parse_message(
    text: str,
    chat_id: int,
    user_id: int | None,
    timezone: str,
    now: datetime | None = None,
) -> ParseResult:
    """Parse a user message and return a structured result.

    Returns one of:
      - CompleteEvent: ready to save immediately
      - IncompleteEvent: start recorded, waiting for end
      - CloseRequest: wants to close an incomplete event (needs confirmation)
      - HelpRequest: message not understood
    """
    if now is None:
        import zoneinfo

        tz = zoneinfo.ZoneInfo(timezone)
        now = datetime.now(tz).replace(second=0, microsecond=0)

    stripped = text.strip()

    # Try each event type
    for etype, pats in PATTERNS.items():
        result = _try_type(etype, pats, stripped, now, chat_id, user_id, timezone)
        if result is not None:
            return result

    return HelpRequest()


# ── Per-type matching ───────────────────────────────────────


def _try_type(
    etype: EventType,
    pats: dict[str, re.Pattern],
    text: str,
    now: datetime,
    chat_id: int,
    user_id: int | None,
    timezone: str,
) -> ParseResult | None:
    """Try to match *text* against patterns for one event type."""

    # Full interval: "сон с 12:30 до 13:55"
    m = pats["from_to"].match(text)
    if m:
        sh, sm, eh, em = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4))
        start_dt = _at_time(now, sh, sm)
        end_dt = _at_time(now, eh, em)
        if end_dt <= start_dt:
            raise ParseError("Время окончания должно быть позже начала.")
        return CompleteEvent(
            event=IntervalEvent(
                event_type=etype,
                start_time=start_dt,
                end_time=end_dt,
                timezone=timezone,
                chat_id=chat_id,
                user_id=user_id,
                raw_text=text,
            )
        )

    # Start at time: "сон с 12:30"
    m = pats["from"].match(text)
    if m:
        h, mn = int(m.group(1)), int(m.group(2))
        ts = _at_time(now, h, mn)
        return IncompleteEvent(
            event=Event(
                event_type=etype,
                timestamp=ts,
                timezone=timezone,
                chat_id=chat_id,
                user_id=user_id,
                raw_text=text,
            )
        )

    # Standalone start: "сон", "поел", "прогулка"
    if pats["standalone_start"].match(text):
        return IncompleteEvent(
            event=Event(
                event_type=etype,
                timestamp=now,
                timezone=timezone,
                chat_id=chat_id,
                user_id=user_id,
                raw_text=text,
            )
        )

    # Until / ended at: "сон до 13:55" or "сон закончился в 13:55"
    for pat_key in ("until", "ended_at"):
        m = pats[pat_key].match(text)
        if m:
            h, mn = int(m.group(1)), int(m.group(2))
            end_dt = _at_time(now, h, mn)
            return CloseRequest(
                event_type=etype,
                end_time=end_dt,
                matched_start=Event(
                    event_type=etype,
                    timestamp=end_dt,
                    timezone=timezone,
                    chat_id=chat_id,
                    user_id=user_id,
                    raw_text=text,
                ),
            )

    # Standalone end: "проснулся", "наелся", "вернулся"
    if pats["standalone_end"].match(text):
        return CloseRequest(
            event_type=etype,
            end_time=now,
            matched_start=Event(
                event_type=etype,
                timestamp=now,
                timezone=timezone,
                chat_id=chat_id,
                user_id=user_id,
                raw_text=text,
            ),
        )

    return None
