"""Telegram bot application setup and startup."""

import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from baby_log.config import Settings
from baby_log.handlers import (
    handle_confirm_callback,
    handle_help,
    handle_message,
    handle_stats_today,
    handle_stats_week,
)
from baby_log.storage import SheetStorage

logger = logging.getLogger(__name__)

_STATS_TODAY = "stats_today"
_STATS_WEEK = "stats_week"


def build_application(settings: Settings) -> Application:
    """Build and configure the Telegram bot application."""
    storage = SheetStorage(
        spreadsheet_id=settings.google_spreadsheet_id,
        service_account_file=settings.google_service_account_file,
    )

    application = Application.builder().token(settings.telegram_bot_token).build()

    # Commands
    application.add_handler(CommandHandler("start", _on_start))
    application.add_handler(CommandHandler("help", handle_help))

    # Stats menu — triggered by "Статистика" text
    async def _stats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show stats menu with today/week options."""
        keyboard = [
            [
                InlineKeyboardButton("Сегодня", callback_data=_STATS_TODAY),
                InlineKeyboardButton("За неделю", callback_data=_STATS_WEEK),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        if update.message:
            await update.message.reply_text("Выберите период:", reply_markup=reply_markup)

    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.Regex(r"^Статистика$") & ~filters.COMMAND,
            _stats_menu,
        )
    )

    # Stats callbacks
    application.add_handler(
        CallbackQueryHandler(
            lambda u, c: handle_stats_today(u, c, storage, settings.baby_log_timezone),
            pattern=_STATS_TODAY,
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            lambda u, c: handle_stats_week(u, c, storage, settings.baby_log_timezone),
            pattern=_STATS_WEEK,
        )
    )

    # Catch-all callback handler for everything else
    async def _catchall_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Route all remaining callback queries."""
        query = update.callback_query
        if not query:
            return
        logger.info("Callback received: data=%r, chat=%s", query.data, query.message.chat.id)
        await handle_confirm_callback(update, context, storage, settings.baby_log_timezone)

    application.add_handler(CallbackQueryHandler(_catchall_callback))

    # All other text messages
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.Regex(r"^Статистика$"),
            lambda u, c: handle_message(u, c, storage, settings.baby_log_timezone),
        )
    )

    # Error handler
    async def _error_handler(update, context):
        logger.error("Unhandled error: %s", context.error, exc_info=context.error)

    application.add_error_handler(_error_handler)

    return application


async def _on_start(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "Привет! Я помогу записывать сон и кормления ребёнка.\n\n"
            "Отправьте команду или нажмите /help для справки."
        )


def main() -> None:
    """Entry point: load settings, build bot, and start polling."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = Settings()
    logger.info("Starting Baby Log bot with timezone %s", settings.baby_log_timezone)

    app = build_application(settings)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
