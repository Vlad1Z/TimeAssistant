
from telebot import types

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