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
                            "gridProperties": {"rowCount": 1000, "columnCount": 7},
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
            range=f"{sheet_name}!A1:G1",
            valueInputOption="RAW",
            body={"values": [_SHEET_HEADER]},
        ).execute()

        logger.info("Created sheet %s", sheet_name)

    # ── public API ─────────────────────────────────────────────

    def append_event(
        self,
        event: Event | IntervalEvent,
    ) -> None:
        """Append a single event row to the daily sheet."""
        if isinstance(event, IntervalEvent):
            day = event.start_time.date()
        else:
            day = event.timestamp.date()

        self._ensure_sheet(day)
        row = event_to_sheet_row(event)
        sheet_name = self._sheet_name(day)

        self._service.spreadsheets().values().append(
            spreadsheetId=self._spreadsheet_id,
            range=f"{sheet_name}!A:G",
            valueInputOption="RAW",
            body={"values": [row]},
        ).execute()

        logger.info("Appended event to %s: %s", sheet_name, row[1])

    def read_events(
        self,
        day: date,
        chat_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Read all events from a daily sheet, optionally filtered by chat_id."""
        sheet_name = self._sheet_name(day)
        try:
            result = (
                self._service.spreadsheets()
                .values()
                .get(
                    spreadsheetId=self._spreadsheet_id,
                    range=f"{sheet_name}!A:G",
                )
                .execute()
            )
        except HttpError:
            return []

        rows = result.get("values", [])
        if not rows:
            return []

        header = rows[0]
        # Normalize header — handle both new (Russian) and legacy (English) headers
        normalized: dict[str, str] = {}
        for col in header:
            normalized[col] = col

        events: list[dict[str, Any]] = []
        for row in rows[1:]:
            if not row:
                continue
            event_dict = dict(zip(header, row, strict=False))
            if chat_id is not None:
                stored_chat = int(event_dict.get("Чат", event_dict.get("chat_id", 0)) or 0)
                if stored_chat != chat_id:
                    continue
            events.append(event_dict)
        return events

    def read_events_range(
        self,
        start_day: date,
        end_day: date,
        chat_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Read events from multiple daily sheets between start_day and end_day."""
        events: list[dict[str, Any]] = []
        current = start_day
        while current <= end_day:
            events.extend(self.read_events(current, chat_id))
            current += timedelta(days=1)
        return events
