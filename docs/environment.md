# Environment Variables

## TELEGRAM_BOT_TOKEN

- **Purpose:** Telegram bot authentication token.
- **Required:** Yes.
- **Secret:** Yes.
- **Safe example:** `123456789:replace-with-real-token`

## BABY_LOG_TIMEZONE

- **Purpose:** IANA timezone for interpreting user-entered times, daily sheet boundaries, and statistics.
- **Required:** Yes.
- **Safe example:** `Asia/Nicosia`

## GOOGLE_SERVICE_ACCOUNT_FILE

- **Purpose:** Path to Google Service Account JSON credentials file.
- **Required:** Yes.
- **Secret:** Yes (the file itself contains credentials).
- **Safe example:** `credentials/service-account.json`

## GOOGLE_SPREADSHEET_ID

- **Purpose:** Google Spreadsheet ID for storing events.
- **Required:** Yes.
- **Safe example:** `1abc123...` (extract from spreadsheet URL)