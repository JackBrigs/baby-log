"""Tests for the message parser."""

import zoneinfo
from datetime import datetime

import pytest

from baby_log.events import (
    EventType,
    IntervalEvent,
)
from baby_log.parser import (
    CloseRequest,
    CompleteEvent,
    HelpRequest,
    IncompleteEvent,
    ParseError,
    get_help_text,
    parse_message,
)

TZ = "Asia/Nicosia"
CHAT_ID = 12345
USER_ID = 67890


def _now() -> datetime:
    """Return a fixed datetime for deterministic tests."""
    return datetime(2024, 7, 10, 14, 30, 0, tzinfo=zoneinfo.ZoneInfo(TZ))


# ── Sleep ───────────────────────────────────────────────────


class TestSleep:
    def test_zasnul(self):
        result = parse_message("заснул", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, IncompleteEvent)
        assert result.event.event_type == EventType.SLEEP

    def test_son(self):
        result = parse_message("сон", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, IncompleteEvent)
        assert result.event.event_type == EventType.SLEEP

    def test_son_with_time(self):
        result = parse_message("сон с 12:30", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, IncompleteEvent)
        assert result.event.timestamp.hour == 12
        assert result.event.timestamp.minute == 30

    def test_son_interval(self):
        result = parse_message("сон с 12:30 до 13:50", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, CompleteEvent)
        assert isinstance(result.event, IntervalEvent)
        assert result.event.start_time.hour == 12
        assert result.event.end_time.hour == 13

    def test_son_until(self):
        result = parse_message("сон до 13:55", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, CloseRequest)
        assert result.end_time.hour == 13
        assert result.end_time.minute == 55

    def test_son_ended_at(self):
        result = parse_message("сон закончился в 13:55", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, CloseRequest)
        assert result.end_time.hour == 13

    def test_prosnulsya(self):
        result = parse_message("проснулся", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, CloseRequest)
        assert result.event_type == EventType.SLEEP

    def test_interval_end_before_start(self):
        with pytest.raises(ParseError):
            parse_message("сон с 14:00 до 13:00", CHAT_ID, USER_ID, TZ, now=_now())

    def test_case_insensitive(self):
        for text in ("Сон", "СОН", "Заснул"):
            result = parse_message(text, CHAT_ID, USER_ID, TZ, now=_now())
            assert isinstance(result, (IncompleteEvent, CloseRequest))


# ── Feeding ─────────────────────────────────────────────────


class TestFeeding:
    def test_poyel(self):
        result = parse_message("поел", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, IncompleteEvent)
        assert result.event.event_type == EventType.FEEDING

    def test_eda(self):
        result = parse_message("еда", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, IncompleteEvent)
        assert result.event.event_type == EventType.FEEDING

    def test_eda_with_time(self):
        result = parse_message("еда с 12:30", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, IncompleteEvent)
        assert result.event.timestamp.hour == 12

    def test_naelnya(self):
        result = parse_message("наелся", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, CloseRequest)
        assert result.event_type == EventType.FEEDING


# ── Walk ────────────────────────────────────────────────────


class TestWalk:
    def test_progulka(self):
        result = parse_message("прогулка", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, IncompleteEvent)
        assert result.event.event_type == EventType.WALK

    def test_progulka_interval(self):
        result = parse_message("прогулка с 16:00 до 17:30", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, CompleteEvent)
        assert isinstance(result.event, IntervalEvent)

    def test_vernulsya(self):
        result = parse_message("вернулся", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, CloseRequest)
        assert result.event_type == EventType.WALK


# ── Invalid input ──────────────────────────────────────────


class TestInvalidInput:
    def test_unknown_command(self):
        result = parse_message("какой-то текст", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, HelpRequest)

    def test_empty_string(self):
        result = parse_message("", CHAT_ID, USER_ID, TZ, now=_now())
        assert isinstance(result, HelpRequest)


# ── Help text ──────────────────────────────────────────────


class TestHelpText:
    def test_help_not_empty(self):
        text = get_help_text()
        assert len(text) > 0
        assert "сон" in text.lower()
        assert "еда" in text.lower()
        assert "прогулка" in text.lower()
