"""Tests for statistics calculation."""

from baby_log.stats import calculate_daily_stats, calculate_weekly_stats


def _event(ts: str, etype: str, detail: str = "") -> dict:
    """Helper to create a minimal event dict with Russian headers."""
    return {"Время": ts, "Тип": etype, "Детали": detail}


class TestDailyStats:
    def test_empty_events(self):
        result = calculate_daily_stats([])
        assert "Нет событий" in result

    def test_sleep_interval(self):
        events = [
            _event(
                "10.07.2024 12:30",
                "Сон",
                "до 10.07.2024 13:50",
            ),
        ]
        result = calculate_daily_stats(events)
        assert "12:30" in result
        assert "1ч 20мин" in result

    def test_feeding(self):
        events = [
            _event("10.07.2024 08:00", "Кормление"),
            _event("10.07.2024 12:00", "Кормление"),
        ]
        result = calculate_daily_stats(events)
        assert "Кормлений: 2" in result

    def test_total_sleep_accumulates(self):
        events = [
            _event("10.07.2024 10:00", "Сон", "до 10.07.2024 11:00"),
            _event("10.07.2024 14:00", "Сон", "до 10.07.2024 15:30"),
        ]
        result = calculate_daily_stats(events)
        assert "2ч 30мин" in result


class TestWeeklyStats:
    def test_empty(self):
        result = calculate_weekly_stats([])
        assert "Нет событий" in result

    def test_multiple_days(self):
        events = [
            _event("09.07.2024 10:00", "Сон", "до 09.07.2024 11:00"),
            _event("10.07.2024 14:00", "Сон", "до 10.07.2024 15:00"),
            _event("10.07.2024 08:00", "Кормление"),
        ]
        result = calculate_weekly_stats(events)
        assert "09.07.2024" in result
        assert "10.07.2024" in result
        assert "За период:" in result
        assert "2ч 0мин сна" in result

    def test_summary_line(self):
        events = [
            _event("10.07.2024 12:00", "Сон", "до 10.07.2024 13:00"),
        ]
        result = calculate_weekly_stats(events)
        assert "📊" in result
