# Baby Log Project Instructions

This file defines project-specific requirements for the Baby Log Telegram bot.

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

Build a Telegram bot that records a child's daily sleep and feeding events.

The primary interaction must be simple enough to use quickly while caring for a child.

## Supported Input

The bot must understand Russian messages case-insensitively and ignore surrounding whitespace.

Initial supported inputs:

- `заснул`
- `сон`
- `проснулся`
- `поел`
- `сон с 12:30 до 13:50`
- `поел в 12:33`

Expected behavior:

- `заснул` records the start of sleep at the current local time.
- `сон` records the start of sleep at the current local time.
- `проснулся` records the end of sleep at the current local time.
- `поел` records a feeding event at the current local time.
- `сон с HH:MM до HH:MM` records a completed sleep interval.
- `поел в HH:MM` records a feeding event at the specified time.

## Bot Response

After a successfully recorded event, reply in Russian:

`Принято! {recorded action and time}`

Examples:

- `Принято! Сон начался в 12:30.`
- `Принято! Сон закончился в 13:50.`
- `Принято! Сон с 12:30 до 13:50.`
- `Принято! Приём пищи в 12:33.`

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
- incomplete sleep sessions;
- feeding times;
- total completed sleep duration;
- number of feeding events.

Do not display raw JSONL data to the user.

## Storage

- Store data in local files.
- Create one event file per local calendar day.
- Use JSON Lines format: one JSON object per line.
- Store files under a configurable data directory.
- Use ISO 8601 timestamps with timezone information.
- Preserve raw user input for diagnostics.
- Keep storage logic separate from Telegram handlers.
- Append events without rewriting unrelated records.
- Create directories and daily files lazily when the first event is recorded.

## Time

- Use timezone-aware datetimes.
- Read the IANA timezone name from configuration.
- Defaulting silently to the host timezone is not allowed.
- For an input containing only `HH:MM`, interpret it as a time on the current local date.
- Validate hours and minutes.
- Reject impossible times.
- For `сон с HH:MM до HH:MM`, reject an end time earlier than the start time in the initial version.
- Crossing midnight can be added later as an explicit feature.

## Event Model

Initial event types:

- `sleep_started`
- `sleep_ended`
- `sleep_interval`
- `feeding`

Every stored event must contain:

- schema version;
- event type;
- event timestamp or interval;
- timezone;
- Telegram chat ID;
- Telegram user ID when available;
- original user text;
- record creation timestamp.

## Architecture

Separate the project into clear responsibilities:

- configuration loading and validation;
- message parsing;
- domain event models;
- file storage;
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
- events are written to the correct daily file;
- current-day statistics work;
- seven-day statistics work;
- all timestamps are timezone-aware;
- Telegram responses are in Russian;
- parsing and statistics have automated tests;
- configured linting and tests pass;
- no secret values are committed.
EOF

cat > projects/baby_log/docs/project-context.md <<'EOF'
# Project Context

## Purpose

Baby Log is a small Telegram bot for recording a child's sleep and feeding schedule.

The main design goal is extremely fast data entry with minimal typing.

## Primary User

The initial version is intended for one family using one Telegram bot.

Events still record Telegram chat and user identifiers so that data ownership remains explicit and future multi-user support is possible.

## Core Use Cases

### Start Sleep

Input:

`заснул`

or:

`сон`

Result:

Record a sleep start event using the current configured local time.

### End Sleep

Input:

`проснулся`

Result:

Record a sleep end event using the current configured local time.

### Completed Sleep Interval

Input:

`сон с 12:30 до 13:50`

Result:

Record a completed sleep interval using the current configured local date.

### Feeding Now

Input:

`поел`

Result:

Record a feeding event using the current configured local time.

### Feeding at a Specified Time

Input:

`поел в 12:33`

Result:

Record a feeding event using the specified time on the current configured local date.

### Statistics

The Telegram interface must provide a `Статистика` button.

The user must be able to request:

- statistics for today;
- statistics for the latest seven calendar days.

## Domain Terms

Use these English terms in code:

- sleep start;
- sleep end;
- sleep interval;
- feeding;
- daily event file;
- daily statistics;
- weekly statistics.

Use natural Russian phrases only in user-facing messages.

## Data Ownership

Every event belongs to a Telegram chat.

Do not mix events from different chats when producing statistics.

## Non-Goals

The initial version is not a medical system and must not provide medical advice.

It is a personal logging tool, not a clinical record.
EOF

cat > projects/baby_log/docs/project-history.md <<'EOF'
# Project History

## Initial Product Decision

The project starts as a local-file Telegram bot for tracking a child's sleep and feeding events.

## Initial Storage Decision

Use one JSON Lines file per local calendar day.

Reasons:

- append-only writes are simple;
- each event remains independently readable;
- daily file rotation is natural;
- weekly statistics can read at most seven daily files;
- no database administration is required for the initial scope.

Reconsider this decision if the project later requires:

- concurrent high-volume writes;
- editing and deleting historical records;
- multiple children;
- complex analytical queries;
- remote or distributed deployment;
- strong transactional guarantees.

## Initial Parsing Decision

Use explicit documented Russian command formats rather than unrestricted natural-language interpretation.

Reasons:

- deterministic behavior;
- simple validation;
- reliable tests;
- fewer incorrect records;
- lower operational complexity.

Additional aliases may be introduced only with tests and documented behavior.

## Initial Time Decision

Use an explicit IANA timezone from configuration.

All stored timestamps must include timezone information.

Times entered without a date belong to the current date in the configured timezone.

Overnight intervals are outside the initial scope.

## Initial User Interface Decision

Use a persistent Telegram reply keyboard for the `Статистика` action.

When statistics are requested, offer separate actions for today and seven days.
EOF

cat > projects/baby_log/docs/environment.md <<'EOF'
# Environment Variables

This file documents configuration names only.

Never store real secret values here.

## TELEGRAM_BOT_TOKEN

Purpose:

Telegram bot authentication token.

Required:

Yes.

Expected format:

A Telegram Bot API token issued by BotFather.

Secret:

Yes.

Safe example:

`123456789:replace-with-real-token`

## BABY_LOG_TIMEZONE

Purpose:

IANA timezone used to interpret user-entered times, determine daily file boundaries, and format statistics.

Required:

Yes.

Safe example:

`Asia/Nicosia`

## BABY_LOG_DATA_DIR

Purpose:

Directory containing daily JSONL event files.

Required:

No.

Recommended default:

`data`

Safe example:

`data`
EOF

cat > projects/baby_log/docs/claude-mistakes.md <<'EOF'
# Claude Mistakes

Record only significant mistakes or incorrect assumptions that may be repeated.

Each entry must use this structure:

## YYYY-MM-DD — Short title

### Incorrect action or assumption

Describe the incorrect result without including secrets or unnecessary session history.

### Root cause

Describe why the mistake occurred.

### Prevention rule

Write one concise, actionable rule that prevents recurrence.

Do not record:

- ordinary typing mistakes;
- temporary command failures;
- exploratory dead ends;
- unverified assumptions;
- full conversation transcripts.
