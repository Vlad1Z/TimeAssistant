from handlers.StartHandler import StartHandler
from datetime import datetime
from telebot import types
from db import save_appointment, get_last_appointment_id, save_message_id_to_db


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
            user_username = message.from_user.username or "❌ Не указан"
            user_id = message.contact.user_id or "Не указан"

            # Сохраняем данные в базу и получаем ID записи
            save_appointment(
                user_id=user_id,
                username=user_username,
                first_name=user_name,
                last_name=message.contact.last_name,
                phone_number=phone_number,
                date=None,
                time=None,
                request_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Форматируем дату и время
                comments=None,
                status="ожидает"
            )
            record_id = get_last_appointment_id(user_id)

            if not record_id:
                self.bot.send_message(
                    message.chat.id,
                    "❌ Произошла ошибка при сохранении записи. Попробуйте позже."
                )
                return

            # Уведомление администратора
            admin_message = (
                f"📩 Запрос на запись (Заявка №{record_id}):\n"
                f"👤 Имя: {message.from_user.first_name or 'Не указано'} {message.from_user.last_name or ''}\n"
                f"📱 Телефон: {phone_number}\n"
                f"📧 Username: @{user_username}\n"
                f"🆔 ID клиента: <code>{user_id}</code>\n\n"
                "💡 Нажмите на одну из кнопок ниже, чтобы записать клиента или написать ему сообщение."
            )

            markup = types.InlineKeyboardMarkup(row_width=2)  # Указываем, что в строке максимум 2 кнопки

            # Добавляем кнопку "Написать сообщение" в отдельной строке
            markup.add(
                types.InlineKeyboardButton("✉️ Написать сообщение", url=f"tg://user?id={user_id}")
            )

            # Добавляем кнопки "Записать" и "Отклонить" в одной строке
            markup.row(
                types.InlineKeyboardButton("📝 Записать", callback_data=f"record_{record_id}"),
                types.InlineKeyboardButton("❌ Отклонить", callback_data=f"cancel_{record_id}")
            )

            # Отправляем сообщение администратору с корректным parse_mode
            sent_message = self.bot.send_message(
                self.admin_chat_id,
                admin_message,
                reply_markup=markup,
                parse_mode="HTML"  # Здесь указываем HTML, чтобы теги корректно обрабатывались
            )

            # Сохраняем message_id в базу данных
            save_message_id_to_db(record_id, sent_message.message_id)

            # Отправляем сообщение пользователю
            self.bot.send_message(
                message.chat.id,
                "💖 Мы свяжемся с вами совсем скоро, чтобы обсудить все детали. 😊\n\n"
                "📱 Номер нужен для связи в мессенджерах, а если не получится, то мы попробуем вам позвонить.\n\n"
                "📋 Вы также можете ознакомиться с краткой информацией о наших процедурах или посетить наши страницы в социальных сетях.",
                parse_mode="HTML"
            )

            # Вызов метода для отображения главного меню
            start_handler = StartHandler(self.bot)
            start_handler.show_main_menu_buttons(message.chat.id)






