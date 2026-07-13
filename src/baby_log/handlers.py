"""Telegram message and callback handlers."""

import logging
from datetime import datetime, timedelta

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from baby_log.events import (
    EVENT_LABELS,
    Event,
    IntervalEvent,
    tracker,
)
from baby_log.parser import (
    CloseRequest,
    CompleteEvent,
    HelpRequest,
    IncompleteEvent,
    ParseError,
    get_help_text,
    parse_message,
)
from baby_log.stats import calculate_daily_stats, calculate_weekly_stats
from baby_log.storage import SheetStorage

logger = logging.getLogger(__name__)

# Pending intervals per chat: (interval, row_number)
_pending: dict[int, tuple[IntervalEvent, int]] = {}


def _get_chat_id(update: Update) -> int:
    """Extract chat_id from an update."""
    if update.effective_chat:
        return update.effective_chat.id
    raise ValueError("Cannot determine chat_id from update")


def _get_user_id(update: Update) -> int | None:
    """Extract user_id from an update."""
    if update.effective_user:
        return update.effective_user.id
    return None


def _fmt(dt) -> str:
    """Format datetime as HH:MM."""
    return dt.strftime("%H:%M")


def _reply_start(event: Event) -> str:
    """Format reply for a start event."""
    label = EVENT_LABELS.get(event.event_type, event.event_type.value)
    return f"Принято! {label} начался в {_fmt(event.timestamp)}."


def _reply_complete(event: Event | IntervalEvent) -> str:
    """Format reply for a complete event."""
    label = EVENT_LABELS.get(event.event_type, event.event_type.value)
    if isinstance(event, IntervalEvent):
        return f"Принято! {label} с {_fmt(event.start_time)} до {_fmt(event.end_time)}."
    return f"Принято! {label} в {_fmt(event.timestamp)}."


async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    storage: SheetStorage,
    timezone: str,
) -> None:
    """Handle a text message from the user."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    chat_id = _get_chat_id(update)
    user_id = _get_user_id(update)

    # Handle stats text commands
    if text.lower() == "статистика за неделю":
        await handle_stats_week_text(update, storage, timezone, chat_id)
        return

    try:
        result = parse_message(text, chat_id, user_id, timezone)
    except ParseError as exc:
        await update.message.reply_text(str(exc))
        return

    if isinstance(result, HelpRequest):
        await update.message.reply_text(get_help_text())
        return

    if isinstance(result, CompleteEvent):
        try:
            storage.append_event(result.event)
        except Exception as exc:
            await update.message.reply_text(f"Ошибка при сохранении: {exc}")
            return
        await update.message.reply_text(_reply_complete(result.event))
        return

    if isinstance(result, IncompleteEvent):
        try:
            row_number = storage.append_event(result.event)
        except Exception as exc:
            await update.message.reply_text(f"Ошибка при сохранении: {exc}")
            return
        tracker.add(chat_id, result.event, row_number=row_number)
        await update.message.reply_text(_reply_start(result.event))
        return

    if isinstance(result, CloseRequest):
        oldest = tracker.get_oldest(chat_id, result.event_type)
        if oldest is None:
            await update.message.reply_text(
                f"Нет незавершённых записей для {EVENT_LABELS[result.event_type]}."
            )
            return

        start_ev, row_number = oldest
        interval = IntervalEvent(
            event_type=result.event_type,
            start_time=start_ev.timestamp,
            end_time=result.end_time,
            timezone=start_ev.timezone,
            chat_id=chat_id,
            user_id=start_ev.user_id,
            raw_text=f"{start_ev.raw_text} -> {text}",
        )

        label = EVENT_LABELS[result.event_type]
        confirm_text = (
            f"Подтвердите {label}:\n  {_fmt(start_ev.timestamp)} – {_fmt(result.end_time)}"
        )
        keyboard = [
            [
                InlineKeyboardButton("✅ Да", callback_data="yes"),
                InlineKeyboardButton("❌ Нет", callback_data="no"),
            ],
        ]
        await update.message.reply_text(
            confirm_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        _pending[chat_id] = (interval, row_number)
        logger.info("Sent confirmation for chat %d, row %d", chat_id, row_number)
        return


async def handle_confirm_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    storage: SheetStorage,
    timezone: str,
) -> None:
    """Handle inline button callbacks for confirm/cancel."""
    query = update.callback_query
    if not query:
        logger.warning("handle_confirm_callback: no callback_query")
        return

    logger.info("handle_confirm_callback: data=%s, chat=%s", query.data, query.message.chat.id)

    await query.answer()

    chat_id = query.message.chat.id

    if query.data == "no":
        _pending.pop(chat_id, None)
        await query.edit_message_text("Отменено.")
        return

    if query.data == "yes":
        pending = _pending.pop(chat_id, None)
        if pending is None:
            logger.warning("No pending interval for chat %d", chat_id)
            await query.edit_message_text("Ошибка: нет данных для сохранения.")
            return

        interval, row_number = pending

        try:
            if row_number:
                storage.update_row(interval.start_time.date(), row_number, interval)
            else:
                storage.append_event(interval)
        except Exception as exc:
            logger.error("Failed to save interval: %s", exc)
            await query.edit_message_text(f"Ошибка при сохранении: {exc}")
            return

        oldest = tracker.get_oldest(chat_id, interval.event_type)
        if oldest:
            tracker.remove(chat_id, oldest[0])

        await query.edit_message_text(_reply_complete(interval))
        return


# ── Stats handlers ───────────────────────────────────────────


async def handle_stats_today(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    storage: SheetStorage,
    timezone: str,
) -> None:
    """Handle the 'stats today' callback."""
    import zoneinfo

    tz = zoneinfo.ZoneInfo(timezone)
    today = datetime.now(tz).date()
    events = storage.read_events(today)
    stats_text = calculate_daily_stats(events)

    reply = f"📊 Статистика за {today.strftime('%d.%m.%Y')}:\n\n{stats_text}"
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(reply)
    elif update.message:
        await update.message.reply_text(reply)


async def handle_stats_week(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    storage: SheetStorage,
    timezone: str,
) -> None:
    """Handle the 'stats week' callback."""
    import zoneinfo

    tz = zoneinfo.ZoneInfo(timezone)
    today = datetime.now(tz).date()
    week_ago = today - timedelta(days=6)
    events = storage.read_events_range(week_ago, today)
    stats_text = calculate_weekly_stats(events)

    reply = (
        f"📊 Статистика за "
        f"{week_ago.strftime('%d.%m.%Y')} – {today.strftime('%d.%m.%Y')}:\n\n"
        f"{stats_text}"
    )
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(reply)
    elif update.message:
        await update.message.reply_text(reply)


async def handle_stats_week_text(
    update: Update,
    storage: SheetStorage,
    timezone: str,
    chat_id: int,
) -> None:
    """Handle 'статистика за неделю' text command."""
    import zoneinfo

    tz = zoneinfo.ZoneInfo(timezone)
    today = datetime.now(tz).date()
    week_ago = today - timedelta(days=6)
    events = storage.read_events_range(week_ago, today)
    stats_text = calculate_weekly_stats(events)

    reply = (
        f"📊 Статистика за "
        f"{week_ago.strftime('%d.%m.%Y')} – {today.strftime('%d.%m.%Y')}:\n\n"
        f"{stats_text}"
    )
    if update.message:
        await update.message.reply_text(reply)


async def handle_help(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle the /help command."""
    if update.message:
        await update.message.reply_text(get_help_text())
