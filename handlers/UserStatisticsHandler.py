from telebot import types
from db import get_unique_users, get_repeat_visits, get_inactive_users


class UserStatisticsHandler:
    def __init__(self, bot):
        self.bot = bot

    def show_statistics(self, message):
        """Отображает главное меню статистики пользователей."""
        unique_users = get_unique_users()
        repeat_visits = get_repeat_visits()
        inactive_users = get_inactive_users()

        unique_count = len(unique_users) if unique_users else 0
        repeat_count = repeat_visits or 0
        inactive_count = len(inactive_users) if inactive_users else 0

        statistics_message = (
            f"📊 <b>Статистика посещений:</b>\n\n"
            f"👥 Уникальные пользователи: {unique_count} [Подробнее]\n"
            f"🔄 Повторные посещения: {repeat_count} [Подробнее]\n"
            f"📭 Неактивные пользователи: {inactive_count} [Подробнее]\n"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("👥 Уникальные пользователи", callback_data="unique_users"))
        markup.add(types.InlineKeyboardButton("🔄 Повторные посещения", callback_data="repeat_visits"))
        markup.add(types.InlineKeyboardButton("📭 Неактивные пользователи", callback_data="inactive_users"))

        self.bot.send_message(
            message.chat.id,
            statistics_message,
            reply_markup=markup,
            parse_mode="HTML"
        )

    def handle_detailed_statistics(self, call):
        """Обрабатывает нажатие на кнопки статистики."""
        if call.data == "unique_users":
            result = get_unique_users()
            if result:
                detail_message = "👥 Уникальные пользователи:\n\n" + "\n".join(
                    [
                        f"👤 <b>{user['first_name']} {user['last_name'] or ''}</b> "
                        f"(ID: <code>{user['telegram_user_id']}</code>) "
                        f"{'@' + user['username'] if user['username'] else ''}"
                        for user in result
                    ]
                )
            else:
                detail_message = "❌ Нет уникальных пользователей."

        elif call.data == "repeat_visits":
            repeat_count = get_repeat_visits()
            detail_message = (
                f"🔄 Пользователи с повторными посещениями: {repeat_count}\n\n"
                "❗ Детальная информация пока недоступна для этой категории."
            )

        elif call.data == "inactive_users":
            result = get_inactive_users()
            if result:
                detail_message = "📭 Неактивные пользователи:\n\n" + "\n".join(
                    [
                        f"👤 <b>{user['first_name']} {user['last_name'] or ''}</b> "
                        f"(ID: <code>{user['telegram_user_id']}</code>) "
                        f"{'@' + user['username'] if user['username'] else ''}"
                        for user in result
                    ]
                )
            else:
                detail_message = "❌ Нет неактивных пользователей."

        elif call.data == "back_to_menu":
            # Возвращение в главное меню
            from handlers.StartHandler import StartHandler
            start_handler = StartHandler(self.bot)
            start_handler.main_menu(call.message)
            return

        # Отправляем сообщение
        self.bot.send_message(
            call.message.chat.id,
            detail_message,
            parse_mode="HTML"
        )
