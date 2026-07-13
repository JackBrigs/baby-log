# Baby Log Project Instructions

## Shared Standards

@../../standards/global/engineering.md
@../../standards/global/task-workflow.md
@../../standards/global/security.md
@../../standards/global/git-workflow.md
@../../standards/languages/python.md

## Project Documentation

@docs/project-context.md
@docs/project-history.md
@docs/environment.md
@docs/claude-mistakes.md

## Language

- Source code, identifiers, comments, documentation, commit messages, and persistent Claude instructions must be written in English.
- User-facing Telegram messages must be written in Russian unless a requirement explicitly says otherwise.
- The user may provide requirements and corrections in Russian.
- When the user provides a durable project rule in Russian, translate its meaning into concise technical English and update the most relevant project documentation file.
- Preserve the user's intent rather than translating word for word.
- Do not store temporary debugging details, uncertain assumptions, or secrets as project knowledge.

## Product Goal

Build a Telegram bot that records a child's daily sleep, feeding, and walk events.

The primary interaction must be simple enough to use quickly while caring for a child.

## Supported Input

The bot must understand Russian messages case-insensitively and ignore surrounding whitespace.

Three event types: sleep, feeding, walk.

Each type supports four input patterns:

| Pattern | Example | Result |
|---|---|---|
| Standalone start | `сон` | Start now |
| Start at time | `сон с 12:30` | Start at given time |
| Full interval | `сон с 12:30 до 13:50` | Complete interval |
| Close incomplete | `сон до 13:55` | Close oldest open event (with confirmation) |

Per-type vocabulary:
- **Sleep**: start — `заснул`, `сон`; end — `проснулся`
- **Feeding**: start — `поел`, `еда`; end — `наелся`
- **Walk**: start — `прогулка`; end — `вернулся`

## Bot Response

After a successfully recorded event, reply in Russian:

`Принято! {recorded action and time}`

For a close request, show a confirmation message with ✅ Да / ❌ Нет buttons.

For invalid or unsupported input:
- do not write an event;
- explain the expected formats briefly;
- keep the response user-friendly and concise.

## Statistics

The bot must provide a persistent Telegram button named `Статистика`.

Statistics must be available for:
- the current local day;
- the latest seven local calendar days, including today.

The statistics response must be readable in Telegram and contain:
- sleep intervals;
- feeding times and count;
- walk count;
- total completed sleep duration.

Do not display raw data to the user.

## Storage

- Store data in Google Sheets.
- Create one sheet tab per local calendar day (tab name = `YYYY-MM-DD`).
- Tab columns (Russian): `Время`, `Тип`, `Детали`, `Чат`, `Пользователь`, `Сообщение`, `Создано`.
- Date/time format: `DD.MM.YYYY HH:MM` (human-readable).
- Use ISO 8601 timestamps with timezone information internally.
- Preserve raw user input for diagnostics.
- Keep storage logic separate from Telegram handlers.
- Append events without rewriting unrelated records.
- Create tabs lazily when the first event is recorded.

## Time

- Use timezone-aware datetimes.
- Read the IANA timezone name from configuration.
- Defaulting silently to the host timezone is not allowed.
- For an input containing only `HH:MM`, interpret it as a time on the current local date.
- Validate hours and minutes.
- Reject impossible times.
- For intervals, reject an end time earlier than or equal to the start time.
- Crossing midnight can be added later as an explicit feature.

## Architecture

Separate the project into clear responsibilities:
- configuration loading and validation;
- message parsing;
- domain event models;
- Google Sheets storage;
- statistics calculation and formatting;
- Telegram handlers;
- application startup.

Telegram handlers must remain thin.
Parsing, storage, and statistics must be testable without Telegram or network access.

## Initial Scope

The first version does not require:
- a database;
- Docker;
- cloud deployment;
- multiple children;
- editing events;
- deleting events;
- authentication beyond Telegram chat identity;
- natural-language parsing beyond the documented formats;
- overnight sleep intervals;
- graphical charts.

Do not add these features unless explicitly requested.

## Definition of Done

A feature is complete only when:
- documented input formats work;
- invalid input does not create records;
- events are written to the correct daily sheet;
- current-day statistics work;
- seven-day statistics work;
- all timestamps are timezone-aware;
- Telegram responses are in Russian;
- parsing and statistics have automated tests;
- configured linting and tests pass;
- no secret values are committed.