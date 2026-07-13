# Project Context

## Purpose

Baby Log is a small Telegram bot for recording a child's sleep and feeding events.

The main design goal is extremely fast data entry with minimal typing.

## Primary User

The initial version is intended for one family using one Telegram bot.

Events still record Telegram chat and user identifiers so that data ownership remains explicit and future multi-user support is possible.

## Core Use Cases

### Start Sleep

Input: `заснул` or `сон`

Result: Record a sleep start event using the current configured local time.

### End Sleep

Input: `проснулся`

Result: Record a sleep end event using the current configured local time.

### Completed Sleep Interval

Input: `сон с 12:30 до 13:50`

Result: Record a completed sleep interval using the current configured local date.

### Feeding Now

Input: `поел`

Result: Record a feeding event using the current configured local time.

### Feeding at a Specified Time

Input: `поел в 12:33`

Result: Record a feeding event using the specified time on the current configured local date.

### Statistics

The Telegram interface provides a `Статистика` button.

The user can request:
- statistics for today;
- statistics for the latest seven calendar days.

## Domain Terms

Use these English terms in code:
- sleep start; sleep end; sleep interval; feeding;
- daily statistics; weekly statistics.

Use natural Russian phrases only in user-facing messages.

## Data Ownership

Every event belongs to a Telegram chat.
Do not mix events from different chats when producing statistics.

## Storage

Events are stored in Google Sheets with one sheet tab per calendar day.
Authentication uses a Google Service Account JSON credential file.

## Non-Goals

The initial version does not require:
- a relational database;
- Docker;
- cloud deployment;
- multiple children;
- editing events;
- deleting events;
- overnight sleep intervals;
- graphical charts.