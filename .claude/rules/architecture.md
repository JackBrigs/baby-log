# Architecture

## Structure

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

## Boundaries

- **config.py** — loads and validates environment variables. No Telegram or Sheets logic.
- **events.py** — pure domain models (Pydantic). No external dependencies.
- **parser.py** — converts user text to structured results. Depends only on events.py.
- **storage.py** — Google Sheets API calls. Depends on events.py for row conversion.
- **stats.py** — calculates statistics from event dicts. Depends on events.py for type labels.
- **handlers.py** — Telegram message/callback handlers. Depends on parser, storage, stats, events.
- **bot.py** — application bootstrap. Depends on all modules.

## Data Flow

```
User message → parser.py → ParseResult
ParseResult → handlers.py → storage.py → Google Sheets
storage.py → stats.py → formatted Russian text → Telegram reply
```

## State

- `IncompleteTracker` in events.py tracks open-ended events per chat (in-memory).
- `_pending` dict in handlers.py stores intervals awaiting user confirmation (in-memory).
- Both are lost on bot restart. This is acceptable for the initial version.