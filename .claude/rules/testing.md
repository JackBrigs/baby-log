# Testing

## Requirements

- Tests must run without Telegram or network access.
- Parsing and statistics must have automated tests.
- Use `pytest` as the test runner.
- Place tests in `tests/`, one file per module.

## Conventions

- Use deterministic fixtures (fixed datetimes) for reproducible results.
- Name test methods after the behavior they verify.
- Group related tests in classes.
- Test both normal and edge cases.

## Coverage

Must be tested:
- **parser.py** — all input formats, all event types, invalid input, case insensitivity, whitespace handling.
- **events.py** — model creation, sheet-row conversion, label roundtrip.
- **stats.py** — daily stats (empty, intervals, started/ended, feedings, walks), weekly stats (multi-day, summary).

Not required for initial version:
- Integration tests for storage (requires real Google Sheets access).
- Handler tests (require Telegram Update mocking).

## Commands

```bash
# Run all tests
PYTHONPATH=src pytest tests/ -v

# Run specific test file
PYTHONPATH=src pytest tests/test_parser.py -v
```