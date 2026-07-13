# Baby Log

Telegram bot for recording a child's daily sleep, feeding, and walk events.

Events are stored in Google Sheets with one tab per calendar day.

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Telegram bot token (from [BotFather](https://t.me/botfather))
- Google Service Account JSON credentials
- Google Spreadsheet with editor access for the service account

### 2. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Configure

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from BotFather |
| `BABY_LOG_TIMEZONE` | IANA timezone (e.g., `Asia/Nicosia`) |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to Service Account JSON |
| `GOOGLE_SPREADSHEET_ID` | Google Spreadsheet ID |

### 4. Run

```bash
python -m baby_log.bot
```

## Supported Commands

All commands are case-insensitive.

### Sleep

| Input | Result |
|---|---|
| `заснул` / `сон` | Start sleep now |
| `сон с 12:30` | Start sleep at 12:30 |
| `сон с 12:30 до 13:50` | Complete sleep interval |
| `сон до 13:55` | Close the last open sleep (with confirmation) |
| `проснулся` | Close the last open sleep (with confirmation) |

### Feeding

| Input | Result |
|---|---|
| `поел` / `еда` | Start feeding now |
| `еда с 12:30` | Start feeding at 12:30 |
| `еда с 12:30 до 13:00` | Complete feeding interval |
| `еда до 13:00` | Close the last open feeding (with confirmation) |
| `наелся` | Close the last open feeding (with confirmation) |

### Walk

| Input | Result |
|---|---|
| `прогулка` | Start walk now |
| `прогулка с 16:00` | Start walk at 16:00 |
| `прогулка с 16:00 до 17:30` | Complete walk interval |
| `прогулка до 17:30` | Close the last open walk (with confirmation) |
| `вернулся` | Close the last open walk (with confirmation) |

### Statistics

Press the `Статистика` button in the keyboard, then choose:
- **Сегодня** — statistics for today
- **За неделю** — statistics for the last 7 days

## Development

```bash
# Run tests
PYTHONPATH=src pytest tests/ -v

# Lint and format
ruff check --fix src/ tests/
ruff format src/ tests/

# Type check
mypy src/
```

## Project Structure

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