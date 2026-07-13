"""Domain event models and sheet-row conversion."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class EventType(StrEnum):
    """Supported event types."""

    SLEEP = "sleep"
    FEEDING = "feeding"
    WALK = "walk"


# Human-readable Russian labels for spreadsheet and messages
EVENT_LABELS = {
    EventType.SLEEP: "Сон",
    EventType.FEEDING: "Кормление",
    EventType.WALK: "Прогулка",
}


class Event(BaseModel):
    """A single-point-in-time event (start or standalone)."""

    schema_version: int = 1
    event_type: EventType
    timestamp: datetime = Field(..., description="Event datetime with timezone")
    timezone: str = Field(..., description="IANA timezone name")
    chat_id: int
    user_id: int | None = None
    raw_text: str = Field(..., description="Original user message text")
    created_at: datetime = Field(default_factory=datetime.now)


class IntervalEvent(BaseModel):
    """A completed interval with start and end times."""

    schema_version: int = 1
    event_type: EventType
    start_time: datetime = Field(..., description="Interval start datetime with tz")
    end_time: datetime = Field(..., description="Interval end datetime with tz")
    timezone: str = Field(..., description="IANA timezone name")
    chat_id: int
    user_id: int | None = None
    raw_text: str = Field(..., description="Original user message text")
    created_at: datetime = Field(default_factory=datetime.now)


# ── Sheet row conversion ────────────────────────────────────

_SHEET_HEADER = [
    "Время",
    "Тип",
    "Детали",
    "Чат",
    "Пользователь",
    "Сообщение",
    "Создано",
]

# Keep old header names for backward compatibility when reading
_LEGACY_HEADER = [
    "timestamp",
    "event_type",
    "detail",
    "timezone",
    "chat_id",
    "user_id",
    "raw_text",
    "created_at",
]


def _fmt_dt(dt: datetime) -> str:
    """Format datetime as DD.MM.YYYY HH:MM for human readability."""
    return dt.strftime("%d.%m.%Y %H:%M")


def event_to_sheet_row(
    event: Event | IntervalEvent,
) -> list[str]:
    """Convert an event model to a flat list for a Google Sheets row."""
    label = EVENT_LABELS.get(event.event_type, event.event_type.value)
    chat = str(event.chat_id)
    user = str(event.user_id) if event.user_id else ""
    raw = event.raw_text
    created = _fmt_dt(event.created_at)

    if isinstance(event, IntervalEvent):
        time_col = _fmt_dt(event.start_time)
        details = f"до {_fmt_dt(event.end_time)}"
    else:
        time_col = _fmt_dt(event.timestamp)
        details = ""

    return [time_col, label, details, chat, user, raw, created]


def sheet_row_to_event_type(row_label: str) -> EventType | None:
    """Reverse-lookup an EventType from its Russian label."""
    for etype, lbl in EVENT_LABELS.items():
        if lbl == row_label:
            return etype
    return None


# ── Parse result types ──────────────────────────────────────


@dataclass
class CompleteEvent:
    """Parser produced a fully-formed event ready to save."""

    event: Event | IntervalEvent


@dataclass
class IncompleteEvent:
    """Parser produced an event missing an end time."""

    event: Event  # the start event


@dataclass
class CloseRequest:
    """Parser wants to close an incomplete event; needs confirmation."""

    event_type: EventType
    end_time: datetime
    matched_start: Event  # the incomplete event being closed


@dataclass
class HelpRequest:
    """Parser could not understand the message."""

    pass


ParseResult = CompleteEvent | IncompleteEvent | CloseRequest | HelpRequest


# ── State tracker for incomplete events ─────────────────────


class IncompleteTracker:
    """Track incomplete (open-ended) events per chat for later closure."""

    def __init__(self) -> None:
        self._store: dict[int, list[Event]] = {}

    def add(self, chat_id: int, event: Event) -> None:
        """Record an incomplete event for a chat."""
        self._store.setdefault(chat_id, []).append(event)

    def get_oldest(self, chat_id: int, event_type: EventType) -> Event | None:
        """Return the oldest incomplete event of the given type for a chat."""
        for ev in self._store.get(chat_id, []):
            if ev.event_type == event_type:
                return ev
        return None

    def remove(self, chat_id: int, event: Event) -> None:
        """Remove a specific incomplete event (after it was closed)."""
        lst = self._store.get(chat_id, [])
        self._store[chat_id] = [e for e in lst if e is not event]

    def clear_chat(self, chat_id: int) -> None:
        """Remove all tracked incomplete events for a chat."""
        self._store.pop(chat_id, None)


# Module-level tracker shared across the bot lifecycle
tracker = IncompleteTracker()
