# Project Context

## Purpose

Baby Log is a Telegram bot for recording a child's daily events: sleep, feeding, and walks.

The primary user is a parent who needs to log events quickly, often one-handed.

## Supported Event Types

| Type | Code | Russian label |
|---|---|---|
| Sleep | `sleep` | Сон |
| Feeding | `feeding` | Кормление |
| Walk | `walk` | Прогулка |

## Input Formats

Each event type supports four input patterns (case-insensitive, whitespace-tolerant):

| Pattern | Example | Result |
|---|---|---|
| Standalone start | `сон` | Record start at current time |
| Start at time | `сон с 12:30` | Record start at given time today |
| Full interval | `сон с 12:30 до 13:50` | Record complete interval |
| Close incomplete | `сон до 13:55` | Close the oldest open event of this type (with confirmation) |

### Per-type vocabulary

- **Sleep**: start — `заснул`, `сон`; end — `проснулся`
- **Feeding**: start — `поел`, `еда`; end — `наелся`
- **Walk**: start — `прогулка`; end — `вернулся`

## Confirmation Flow

When the user sends a close command (e.g., `сон до 13:55`), the bot:

1. Finds the oldest incomplete event of that type for the chat.
2. Shows a confirmation message with the proposed interval.
3. Waits for the user to press ✅ Да or ❌ Нет.
4. On yes — saves the interval to Google Sheets and removes the start event from the tracker.
5. On no — discards the pending interval.

## Storage

- Google Sheets, one tab per calendar day (tab name = `YYYY-MM-DD`).
- Tab columns (Russian headers): `Время`, `Тип`, `Детали`, `Чат`, `Пользователь`, `Сообщение`, `Создано`.
- Date/time format: `DD.MM.YYYY HH:MM` (human-readable).
- Authentication: Google Service Account JSON.
- Append-only — no edits or deletes.

## Statistics

Available via the `Статистика` persistent keyboard button:
- **Today**: sleep intervals, feeding count, walk count, total sleep.
- **Last 7 days**: same metrics grouped by day with a period summary.

Events from different chats are never mixed.

## Architecture

```
src/baby_log/
├── bot.py         — application setup, polling loop
├── config.py      — settings from environment (pydantic-settings)
├── events.py      — domain models, sheet-row conversion, incomplete tracker
├── handlers.py    — Telegram message and callback handlers
├── parser.py      — Russian message parser, pattern matching
├── stats.py       — daily and weekly statistics calculation
└── storage.py     — Google Sheets read/write
```

Parsing, storage, and statistics are testable without Telegram or network access.

## Time

- IANA timezone from `BABY_LOG_TIMEZONE` (default: `Asia/Nicosia`).
- All stored timestamps are timezone-aware.
- Times without a date belong to the current date in the configured timezone.
- Overnight intervals are not supported in the initial version.

## Non-Goals

- Relational database, Docker, cloud deployment.
- Multiple children, editing or deleting events.
- Overnight sleep intervals, graphical charts.
- Authentication beyond Telegram chat identity.