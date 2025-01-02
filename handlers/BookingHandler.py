from telebot import types
from datetime import datetime
from db import save_appointment, update_appointment, get_user_data_by_record_id
from config import id_chat_owner


class BookingHandler:
    def __init__(self, bot, start_handler):
        self.bot = bot
        self.start_handler = start_handler  # Сохраняем ссылку на start_handler
        self.selected_date = None
        self.selected_time = None
        self.comments = None

    def start_admin_booking(self, call, record_id):
        """Начинает процесс записи администратора для клиента."""
        self.current_record_id = record_id  # Сохраняем текущий ID записи

        # Отправляем вопрос и сохраняем ID сообщения
        bot_message = self.bot.send_message(
            call.message.chat.id,
            "📅 Укажите дату (ДД.ММ.ГГ):",
            reply_markup=types.ForceReply(selective=True)  # ForceReply для скрытия текста
        )
        self.last_bot_message_id = bot_message.message_id  # Сохраняем ID сообщения
        self.bot.register_next_step_handler(bot_message, self.process_admin_date)

    def process_admin_date(self, message):
        """Обрабатывает ввод даты администратором."""
        try:
            self.selected_date = datetime.strptime(message.text, '%d.%m.%y').date()
            if self.selected_date < datetime.today().date():
                raise ValueError("Дата не может быть в прошлом.")

            # Удаляем предыдущее сообщение (вопрос и ответ)
            self.bot.delete_message(message.chat.id, message.message_id)
            if hasattr(self, 'last_bot_message_id') and self.last_bot_message_id:
                self.bot.delete_message(message.chat.id, self.last_bot_message_id)

            # Задаем новый вопрос
            bot_message = self.bot.send_message(
                message.chat.id,
                "⏰ Укажите время (ЧЧ:ММ):",
                reply_markup=types.ForceReply(selective=True)
            )
            self.last_bot_message_id = bot_message.message_id  # Сохраняем ID сообщения
            self.bot.register_next_step_handler(bot_message, self.process_admin_time)
        except ValueError:
            # Удаляем сообщение с ошибкой, если оно было
            self.bot.delete_message(message.chat.id, message.message_id)
            if hasattr(self, 'last_bot_message_id') and self.last_bot_message_id:
                self.bot.delete_message(message.chat.id, self.last_bot_message_id)

            bot_message = self.bot.send_message(
                message.chat.id,
                "❌ Неверный формат даты. Введите дату (ДД.ММ.ГГ):",
                reply_markup=types.ForceReply(selective=True)
            )
            self.last_bot_message_id = bot_message.message_id
            self.bot.register_next_step_handler(bot_message, self.process_admin_date)

    def process_admin_time(self, message):
        """Обрабатывает ввод времени администратором."""
        try:
            self.selected_time = message.text
            # Преобразуем введённое время в формат ЧЧ:ММ
            self.selected_time = datetime.strptime(self.selected_time, '%H:%M').strftime('%H:%M')

            # Удаляем предыдущее сообщение (вопрос и ответ)
            self.bot.delete_message(message.chat.id, message.message_id)
            if hasattr(self, 'last_bot_message_id') and self.last_bot_message_id:
                self.bot.delete_message(message.chat.id, self.last_bot_message_id)

            # Задаем новый вопрос
            bot_message = self.bot.send_message(
                message.chat.id,
                "💬 Укажите комментарий:",
                reply_markup=types.ForceReply(selective=True)
            )
            self.last_bot_message_id = bot_message.message_id  # Сохраняем ID сообщения
            self.bot.register_next_step_handler(bot_message, self.process_admin_comment)
        except ValueError:
            # Удаляем сообщение с ошибкой
            self.bot.delete_message(message.chat.id, message.message_id)
            if hasattr(self, 'last_bot_message_id') and self.last_bot_message_id:
                self.bot.delete_message(message.chat.id, self.last_bot_message_id)

            bot_message = self.bot.send_message(
                message.chat.id,
                "❌ Неверный формат времени. Введите время (ЧЧ:ММ):",
                reply_markup=types.ForceReply(selective=True)
            )
            self.last_bot_message_id = bot_message.message_id
            self.bot.register_next_step_handler(bot_message, self.process_admin_time)

    def process_admin_comment(self, message):
        """Обрабатывает ввод комментария администратором."""
        self.comments = message.text

        # Удаляем предыдущее сообщение (вопрос и ответ)
        self.bot.delete_message(message.chat.id, message.message_id)
        if hasattr(self, 'last_bot_message_id') and self.last_bot_message_id:
            self.bot.delete_message(message.chat.id, self.last_bot_message_id)

        # Получаем данные пользователя из базы
        user_data = get_user_data_by_record_id(self.current_record_id)

        if not user_data:
            self.bot.send_message(
                message.chat.id,
                "❌ Ошибка: Данные пользователя не найдены."
            )
            return

        # Отправляем сообщение с подтверждением
        confirmation_message = (
            f"📩 Запрос на запись (Заявка №{self.current_record_id}):\n\n"
            f"👤 Имя: {user_data['first_name'] or 'Не указано'} {user_data['last_name'] or ''}\n"
            f"📱 Телефон: {user_data['phone_number'] or 'Не указан'}\n"
            f"📧 Username: @{user_data['username'] or 'Не указан'}\n"
            f"🆔 ID клиента: <code>{user_data['telegram_user_id']}</code>\n\n"
            f"Данные для записи:\n"
            f"📅 Дата: {self.selected_date.strftime('%d.%m.%y')}\n"
            f"⏰ Время: {self.selected_time}\n"
            f"💬 Комментарий: {self.comments}\n\n"
            "✅ Нажмите 'Подтвердить', чтобы сохранить запись, или '❌ Отменить', чтобы отказаться."
        )

        # Создаем инлайн-кнопки
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_booking"),
            types.InlineKeyboardButton("❌ Отменить", callback_data="cancel_booking")
        )

        # Отправляем сообщение с кнопками
        sent_message = self.bot.send_message(
            message.chat.id,
            confirmation_message,
            reply_markup=markup,
            parse_mode="HTML"  # Указываем HTML для обработки тега <code>
        )

        self.last_bot_message_id = sent_message.message_id  # Сохраняем ID сообщения

