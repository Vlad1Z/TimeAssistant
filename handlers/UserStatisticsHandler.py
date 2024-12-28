from telebot import types
from db import get_unique_users, get_repeat_visits, get_inactive_users


class UserStatisticsHandler:
    def __init__(self, bot):
        self.bot = bot

    def show_statistics(self, message):
        """Отображает меню статистики пользователей с кнопками."""
        statistics = self.generate_statistics()

        # Создаём кнопки для подробной информации
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("👥 Уникальные пользователи", callback_data="unique_users"))
        markup.add(types.InlineKeyboardButton("🔄 Повторные посещения", callback_data="repeat_visits"))
        markup.add(types.InlineKeyboardButton("📭 Неактивные пользователи", callback_data="inactive_users"))

        # Отправляем сообщение с кнопками
        self.bot.send_message(
            message.chat.id,
            statistics,
            reply_markup=markup,
            parse_mode="HTML"
        )

    def generate_statistics(self):
        """Генерирует текст для статистики пользователей."""
        return (
            f"📊 <b>Статистика посещений:</b>\n\n"
            f"👥 Уникальные пользователи: [Нажмите кнопку]\n"
            f"🔄 Повторные посещения: [Нажмите кнопку]\n"
            f"📭 Неактивные пользователи: [Нажмите кнопку]\n"
        )

    def handle_detailed_statistics(self, call):
        """Обрабатывает кнопки статистики и выводит детальную информацию."""
        if call.data == "unique_users":
            result = get_unique_users()
            if result:
                detail_message = "👥 Уникальные пользователи:\n" + "\n".join(
                    [f"👤 <b>{user['first_name']} {user['last_name'] or ''}</b> "
                     f"(ID: <code>{user['telegram_user_id']}</code>)"
                     for user in result]
                )
            else:
                detail_message = "❌ Нет уникальных пользователей."

        elif call.data == "repeat_visits":
            result = get_repeat_visits()
            if result:
                detail_message = "🔄 Повторные посещения:\n" + "\n".join(
                    [f"👤 <b>{user['first_name']} {user['last_name'] or ''}</b> "
                     f"(ID: <code>{user['telegram_user_id']}</code>)"
                     for user in result]
                )
            else:
                detail_message = "❌ Нет повторных посещений."

        elif call.data == "inactive_users":
            result = get_inactive_users()
            if result:
                detail_message = "📭 Неактивные пользователи (больше 30 дней):\n" + "\n".join(
                    [f"👤 <b>{user['first_name']} {user['last_name'] or ''}</b> "
                     f"(ID: <code>{user['telegram_user_id']}</code>)"
                     for user in result]
                )
            else:
                detail_message = "❌ Нет неактивных пользователей."

        # Отправляем сообщение с подробной информацией
        self.bot.send_message(
            call.message.chat.id,
            detail_message,
            parse_mode="HTML"
        )
