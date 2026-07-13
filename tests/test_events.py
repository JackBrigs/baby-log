"""Tests for event models and sheet row conversion."""

import zoneinfo
from datetime import datetime

from baby_log.events import (
    EVENT_LABELS,
    Event,
    EventType,
    IntervalEvent,
    event_to_sheet_row,
    sheet_row_to_event_type,
)


def _tz():
    return zoneinfo.ZoneInfo("Asia/Nicosia")


class TestEventLabels:
    def test_all_types_have_labels(self):
        for etype in EventType:
            assert etype in EVENT_LABELS
            assert isinstance(EVENT_LABELS[etype], str)
            assert len(EVENT_LABELS[etype]) > 0

    def test_label_roundtrip(self):
        for etype, label in EVENT_LABELS.items():
            assert sheet_row_to_event_type(label) == etype


class TestEventToSheetRow:
    def test_start_event(self):
        event = Event(
            event_type=EventType.SLEEP,
            timestamp=datetime(2024, 7, 10, 12, 30, tzinfo=_tz()),
            timezone="Asia/Nicosia",
            chat_id=123,
            user_id=456,
            raw_text="сон",
        )
        row = event_to_sheet_row(event)
        assert len(row) == 7
        assert "10.07.2024 12:30" in row[0]
        assert row[1] == "Сон"
        assert row[3] == "123"

    def test_interval_event(self):
        event = IntervalEvent(
            event_type=EventType.SLEEP,
            start_time=datetime(2024, 7, 10, 12, 30, tzinfo=_tz()),
            end_time=datetime(2024, 7, 10, 13, 50, tzinfo=_tz()),
            timezone="Asia/Nicosia",
            chat_id=123,
            raw_text="сон с 12:30 до 13:50",
        )
        row = event_to_sheet_row(event)
        assert row[1] == "Сон"
        assert "до" in row[2]
        assert "13:50" in row[2]

    def test_feeding(self):
        event = Event(
            event_type=EventType.FEEDING,
            timestamp=datetime(2024, 7, 10, 8, 15, tzinfo=_tz()),
            timezone="Asia/Nicosia",
            chat_id=789,
            raw_text="поел",
        )
        row = event_to_sheet_row(event)
        assert row[1] == "Кормление"
        assert "08:15" in row[0]

    def test_none_user_id(self):
        event = Event(
            event_type=EventType.SLEEP,
            timestamp=datetime(2024, 7, 10, 12, 0, tzinfo=_tz()),
            timezone="Asia/Nicosia",
            chat_id=100,
            user_id=None,
            raw_text="сон",
        )
        row = event_to_sheet_row(event)
        assert row[4] == ""
