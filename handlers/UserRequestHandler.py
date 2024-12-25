from telebot import types

class UserRequestHandler:
    def __init__(self, bot, admin_chat_id):
        self.bot = bot
        self.admin_chat_id = admin_chat_id

    def start_request(self, message):
        """Запрашивает у пользователя номер телефона для связи."""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        button = types.KeyboardButton("📞 Отправить номер телефона", request_contact=True)
        markup.add(button)

        self.bot.send_message(
            message.chat.id,
            "📋 Пожалуйста, оставьте ваш номер телефона, чтобы мы могли с вами связаться. 😊",
            reply_markup=markup
        )

    def handle_contact(self, message):
        """Обрабатывает контакт, отправленный пользователем."""
        if message.contact:
            phone_number = message.contact.phone_number
            user_name = message.contact.first_name or "Пользователь"
            user_username = message.from_user.username or "❌ Не указан"  # Извлекаем username из from_user
            user_id = message.contact.user_id

            # Уведомление администратора
            admin_message = (
                f"📩 Запрос на запись:\n"
                f"👤 Имя: {user_name}\n"
                f"📱 Телефон: {phone_number}\n"
                f"📧 Username: {user_username}\n"
                f"🆔 ID клиента: {user_id}\n\n"
                "💡 Нажмите на одну из кнопок ниже, чтобы записать клиента или написать ему сообщение."
            )

            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("📝 Записать", callback_data=f"record_user_{user_id}"),
                types.InlineKeyboardButton("✉️ Написать сообщение", url=f"tg://user?id={user_id}")
            )

            self.bot.send_message(self.admin_chat_id, admin_message, reply_markup=markup)

            # Подтверждение клиенту
            self.bot.send_message(
                message.chat.id,
                "✅ Спасибо за ваш номер! Мы свяжемся с вами в ближайшее время, чтобы обсудить детали записи. 😊",
                reply_markup=types.ReplyKeyboardRemove()
            )
        else:
            # Сообщение клиенту, если контакт не отправлен
            self.bot.send_message(
                message.chat.id,
                "❌ Не удалось получить ваш номер телефона. Пожалуйста, попробуйте снова. 📞"
            )


