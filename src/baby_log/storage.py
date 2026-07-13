"""Google Sheets storage backend."""

import logging
from datetime import date, timedelta
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from baby_log.events import (
    _SHEET_HEADER,
    Event,
    IntervalEvent,
    event_to_sheet_row,
)

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetStorage:
    """Append-only Google Sheets storage with one sheet per calendar day."""

    def __init__(
        self,
        spreadsheet_id: str,
        service_account_file: str,
    ) -> None:
        self._spreadsheet_id = spreadsheet_id
        self._creds = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=SCOPES,
        )
        self._service = build("sheets", "v4", credentials=self._creds)

    # ── helpers ────────────────────────────────────────────────

    def _sheet_name(self, day: date) -> str:
        """Return the sheet tab name for a calendar day, e.g. '2024-07-10'."""
        return day.isoformat()

    def _ensure_sheet(self, day: date) -> None:
        """Create the daily sheet if it does not yet exist, including header."""
        sheet_name = self._sheet_name(day)
        spreadsheets = self._service.spreadsheets()

        # Check if sheet already exists
        metadata = spreadsheets.get(spreadsheetId=self._spreadsheet_id).execute()
        for sheet in metadata.get("sheets", []):
            if sheet["properties"]["title"] == sheet_name:
                return

        # Create new sheet
        create_body = {
            "requests": [
                {
                    "addSheet": {
                        "properties": {
                            "title": sheet_name,
                            "gridProperties": {"rowCount": 1000, "columnCount": 4},
                        }
                    }
                }
            ]
        }
        spreadsheets.batchUpdate(
            spreadsheetId=self._spreadsheet_id,
            body=create_body,
        ).execute()

        # Write header row
        self._service.spreadsheets().values().update(
            spreadsheetId=self._spreadsheet_id,
            range=f"{sheet_name}!A1:D1",
            valueInputOption="RAW",
            body={"values": [_SHEET_HEADER]},
        ).execute()

        logger.info("Created sheet %s", sheet_name)

    # ── public API ─────────────────────────────────────────────

    def append_event(
        self,
        event: Event | IntervalEvent,
    ) -> int:
        """Append a single event row to the daily sheet. Returns the 1-based row number."""
        if isinstance(event, IntervalEvent):
            day = event.start_time.date()
        else:
            day = event.timestamp.date()

        self._ensure_sheet(day)
        row = event_to_sheet_row(event)
        sheet_name = self._sheet_name(day)

        resp = (
            self._service.spreadsheets()
            .values()
            .append(
                spreadsheetId=self._spreadsheet_id,
                range=f"{sheet_name}!A:D",
                valueInputOption="RAW",
                body={"values": [row]},
            )
            .execute()
        )

        row_number: int = 0
        # updatedRows is 1, but we need the actual row index
        # The update range tells us the row
        update_range = resp.get("updates", {}).get("updatedRange", "")
        if update_range:
            # range looks like "2026-07-13!A10:D10"
            parts = update_range.split("!")
            if len(parts) == 2:
                range_part = parts[1]
                # extract row number from A10:D10
                import re

                m = re.search(r"(\d+)", range_part)
                if m:
                    row_number = int(m.group(1))

        logger.info("Appended event to %s row %d: %s", sheet_name, row_number, row[0])
        return row_number

    def update_row(
        self,
        day: date,
        row_number: int,
        event: Event | IntervalEvent,
    ) -> None:
        """Update an existing row in the daily sheet with new event data."""
        row = event_to_sheet_row(event)
        sheet_name = self._sheet_name(day)

        self._service.spreadsheets().values().update(
            spreadsheetId=self._spreadsheet_id,
            range=f"{sheet_name}!A{row_number}:D{row_number}",
            valueInputOption="RAW",
            body={"values": [row]},
        ).execute()

        logger.info("Updated row %d in %s: %s", row_number, sheet_name, row[0])

    def read_events(
        self,
        day: date,
    ) -> list[dict[str, Any]]:
        """Read all events from a daily sheet."""
        sheet_name = self._sheet_name(day)
        try:
            result = (
                self._service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self._spreadsheet_id,
                    range=f"{sheet_name}!A:D",
                )
                .execute()
            )
        except HttpError:
            return []

        rows = result.get("values", [])
        if not rows:
            return []

        header = rows[0]
        events: list[dict[str, Any]] = []
        for row in rows[1:]:
            if not row:
                continue
            event_dict = dict(zip(header, row, strict=False))
            events.append(event_dict)
        return events

    def read_events_range(
        self,
        start_day: date,
        end_day: date,
    ) -> list[dict[str, Any]]:
        """Read events from multiple daily sheets between start_day and end_day."""
        events: list[dict[str, Any]] = []
        current = start_day
        while current <= end_day:
            events.extend(self.read_events(current))
            current += timedelta(days=1)
        return events
