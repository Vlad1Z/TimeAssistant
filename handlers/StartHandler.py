from telebot import types
from config import id_chat_owner
from db import log_user_action


class StartHandler:
    def __init__(self, bot):
        self.bot = bot

    def main_menu(self, message):
        """Отображает главное меню для админа или пользователя."""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        # Проверка, кто отправил команду
        if str(message.chat.id) == id_chat_owner:
            # Меню для админа
            markup.add("📝 Виды процедур", "📋 Отобразить записи", "👥 Посмотреть пользователей")
            welcome_text = (
                "👨‍💼 Здравствуйте, Администратор! Я помогу вам управлять записями и пользователями.\n\n"
                "Выберите одну из опций ниже, чтобы продолжить."
            )
        else:
            # Меню для пользователя
            markup.add("💆‍♀️ Виды процедур", "📅 Узнать о свободных слотах", "🌐 Другие соц сети")
            welcome_text = (
                "👋 Приветствуем вас! Я ваш личный помощник. 🤖\n\n"
                "Готов помочь вам с записью на процедуры и предоставить всю информацию о наших услугах! 😊\n\n"
                "Выберите одну из опций ниже, чтобы продолжить:👇"
            )

        # Логирование действия пользователя
        log_user_action(
            user_id=message.chat.id,
            username=message.from_user.username,
            action_type="start",
            action_details="main_menu"
        )

        # Отправка сообщения с кнопками
        self.bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

