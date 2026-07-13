"""Tests for statistics calculation."""

from baby_log.stats import calculate_daily_stats, calculate_weekly_stats


def _event(start: str, etype: str, end: str = "") -> dict:
    """Helper to create a minimal event dict matching sheet headers."""
    return {
        "тип активности": etype,
        "Дата и время начала": start,
        "дата и время окончания": end,
    }


class TestDailyStats:
    def test_empty_events(self):
        result = calculate_daily_stats([])
        assert "Нет событий" in result

    def test_sleep_interval(self):
        events = [
            _event("10.07.2024 12:30", "Сон", "10.07.2024 13:50"),
        ]
        result = calculate_daily_stats(events)
        assert "Сон" in result
        assert "12:30" in result
        assert "1ч 20мин" in result

    def test_feeding(self):
        events = [
            _event("10.07.2024 08:00", "Кормление", "10.07.2024 08:20"),
            _event("10.07.2024 12:00", "Кормление", "10.07.2024 12:15"),
        ]
        result = calculate_daily_stats(events)
        assert "Кормление" in result
        assert "35мин" in result

    def test_incomplete_sleep(self):
        events = [
            _event("10.07.2024 22:00", "Сон"),  # no end time
        ]
        result = calculate_daily_stats(events)
        assert "Сон" in result
        assert "22:00" in result
        assert "начался" in result

    def test_mixed_completed_and_incomplete(self):
        events = [
            _event("10.07.2024 12:30", "Сон", "10.07.2024 13:50"),
            _event("10.07.2024 22:00", "Сон"),  # no end time
        ]
        result = calculate_daily_stats(events)
        assert "Сон" in result
        assert "12:30 – 13:50" in result
        assert "22:00 (начался)" in result
        assert "1ч 20мин" in result

    def test_incomplete_not_counted_in_total(self):
        events = [
            _event("10.07.2024 22:00", "Сон"),  # no end time
        ]
        result = calculate_daily_stats(events)
        assert "Общее время" not in result

    def test_total_sleep_accumulates(self):
        events = [
            _event("10.07.2024 10:00", "Сон", "10.07.2024 11:00"),
            _event("10.07.2024 14:00", "Сон", "10.07.2024 15:30"),
        ]
        result = calculate_daily_stats(events)
        assert "2ч 30мин" in result


class TestWeeklyStats:
    def test_empty(self):
        result = calculate_weekly_stats([])
        assert "Нет событий" in result

    def test_multiple_days(self):
        events = [
            _event("09.07.2024 10:00", "Сон", "09.07.2024 11:00"),
            _event("10.07.2024 14:00", "Сон", "10.07.2024 15:00"),
            _event("10.07.2024 08:00", "Кормление", "10.07.2024 08:20"),
        ]
        result = calculate_weekly_stats(events)
        assert "09.07.2024" in result
        assert "10.07.2024" in result
        assert "Итого за период:" in result
        assert "Сон: 2ч" in result

    def test_summary_line(self):
        events = [
            _event("10.07.2024 12:00", "Сон", "10.07.2024 13:00"),
        ]
        result = calculate_weekly_stats(events)
        assert "📊" in result

    def test_incomplete_shown_in_weekly(self):
        events = [
            _event("10.07.2024 22:00", "Сон"),  # no end time
        ]
        result = calculate_weekly_stats(events)
        assert "Сон" in result
        assert "22:00" in result
        assert "начался" in result
