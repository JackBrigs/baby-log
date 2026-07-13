# Ошибки и корректирующие правила Claude

Назначение: фиксация существенных ошибок, неверных предположений и правил, предотвращающих их повторение.

## 2026-07-13 — Callback-кнопки не работали

### Incorrect action

Callback-кнопки ✅ Да / ❌ Нет не реагировали на нажатие. Проблема проявлялась несколько раз:
1. Сначала callback handler не был зарегистрирован правильно (использовался `handle_callback` вместо `handle_confirm_callback`).
2. Данные хранились в `context.user_data`, который терялся между запросами.
3. `run_polling()` запускался без `allowed_updates`, поэтому callback-запросы вообще не доставлялись боту.
4. `CallbackQueryHandler` без `pattern` не работал надёжно.
5. После рефакторинга была потеряна функция `_reply_start`.

### Root cause

- Неверное понимание жизненного цикла `context.user_data` в python-telegram-bot.
- Незнание, что `run_polling()` по умолчанию не запрашивает callback-обновления.
- Отсутствие тестирования после рефакторинга.

### Prevention rule

- Для хранения данных между запросами используйте глобальный словарь по chat_id, а не `context.user_data`.
- Всегда передавайте `allowed_updates=Update.ALL_TYPES` в `app.run_polling()`.
- `CallbackQueryHandler` должен иметь явный `pattern` или быть catch-all.
- После рефакторинга проверяйте, что все функции существуют и импортируются.
- Тестируйте изменения перед тем, как отдавать пользователю.

## 2026-07-13 — Spreadsheet ID не совпадал

### Incorrect action

Бот писал в одну таблицу, пользователь смотрел в другую. Spreadsheet ID в `.env` не совпадал с реальной таблицей.

### Root cause

Использовал ID из `.env.example` вместо ID из реальной ссылки пользователя.

### Prevention rule

При получении ссылки на таблицу от пользователя всегда извлекайте ID из URL и сверяйте с `.env`.

## 2026-07-13 — Google Sheets API не был включён

### Incorrect action

Бот получал ошибку 403 SERVICE_DISABLED при попытке записать в таблицу.

### Root cause

Google Sheets API не был включён в Google Cloud проекте.

### Prevention rule

При настройке Service Account всегда проверяйте, что Google Sheets API включён в проекте.