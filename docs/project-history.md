# Project History

## Initial Product Decision

The project starts as a Google Sheets–backed Telegram bot for tracking a child's sleep and feeding events.

## Storage Decision — Google Sheets

Use Google Sheets with one sheet tab per local calendar day.

Reasons:
- append-only writes are simple;
- each event remains independently readable;
- daily sheet rotation is natural;
- weekly statistics can read at most seven daily sheets;
- no database administration is required for the initial scope.

Authentication via Google Service Account JSON credentials.

## Initial Parsing Decision

Use explicit documented Russian command formats rather than unrestricted natural-language interpretation.

## Initial Time Decision

Use an explicit IANA timezone from configuration.
All stored timestamps include timezone information.
Times entered without a date belong to the current date in the configured timezone.
Overnight intervals are outside the initial scope.

## Initial User Interface Decision

Use a persistent Telegram reply keyboard for the `Статистика` action.
When statistics are requested, offer separate actions for today and seven days.