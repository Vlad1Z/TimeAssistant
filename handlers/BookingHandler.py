from telebot import types
from datetime import datetime
from db import save_appointment
from config import id_chat_owner
from db import update_appointment
from db import get_user_data_by_record_id




class BookingHandler:
    def __init__(self, bot, start_handler):
        self.bot = bot
        self.start_handler = start_handler  # Сохраняем ссылку на start_handler
        self.selected_date = None
        self.selected_time = None
        self.comments = None

    def start_booking(self, message):
        """Начинает процесс записи клиента."""
        self.bot.send_message(
            message.chat.id,
            "Выберите дату для записи 🗓️"
        )
        self.bot.register_next_step_handler(message, self.handle_date_selection)

    def start_admin_booking(self, call, record_id):
        """Начинает процесс записи администратора для клиента."""
        self.current_record_id = record_id  # Сохраняем текущий ID записи
        self.bot.send_message(
            call.message.chat.id,
            "📅 Укажите дату для записи (в формате ДД.ММ.ГГ):"
        )
        self.bot.register_next_step_handler(call.message, self.process_admin_date)

    def process_admin_date(self, message):
        """Обрабатывает ввод даты администратором."""
        try:
            self.selected_date = datetime.strptime(message.text, '%d.%m.%y').date()
            if self.selected_date < datetime.today().date():
                raise ValueError("Дата не может быть в прошлом.")
            self.bot.send_message(
                message.chat.id,
                f"Вы выбрали дату: {self.selected_date.strftime('%d.%m.%y')} 🗓️. Теперь укажите время (в формате ЧЧ:ММ):"
            )
            self.bot.register_next_step_handler(message, self.process_admin_time)
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Неверный формат даты или дата в прошлом. Укажите дату в формате ДД.ММ.ГГ."
            )
            self.bot.register_next_step_handler(message, self.process_admin_date)

    def process_admin_time(self, message):
        """Обрабатывает ввод времени администратором."""
        try:
            self.selected_time = message.text
            datetime.strptime(self.selected_time, '%H:%M')  # Проверка формата времени
            self.bot.send_message(
                message.chat.id,
                f"Вы выбрали время: {self.selected_time} ⏰. Теперь добавьте комментарий (например, вид процедуры):"
            )
            self.bot.register_next_step_handler(message, self.process_admin_comment)
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "❌ Неверный формат времени. Укажите время в формате ЧЧ:ММ. Например: 09:00."
            )
            self.bot.register_next_step_handler(message, self.process_admin_time)

    def process_admin_comment(self, message):
        """Обрабатывает ввод комментария администратором и отправляет данные на подтверждение."""
        self.comments = message.text

        # Извлекаем данные пользователя из базы
        from db import get_user_data_by_record_id
        user_data = get_user_data_by_record_id(self.current_record_id)

        # Проверяем, нашли ли данные
        if not user_data:
            self.bot.send_message(message.chat.id, "❌ Ошибка: Данные пользователя не найдены.")
            return

        # Формируем сообщение с профилем пользователя
        profile_data = (
            f"📩 Запрос на запись:\n"
            f"👤 Имя: {user_data['first_name'] or 'Не указано'} {user_data['last_name'] or ''}\n"
            f"📱 Телефон: {user_data['phone_number'] or 'Не указан'}\n"
            f"📧 Username: {user_data['username'] or 'Не указан'}\n"
            f"🆔 ID клиента: {user_data['telegram_user_id']}\n\n"
        )

        # Формируем данные, введённые администратором
        admin_input_data = (
            f"📅 Дата: {self.selected_date.strftime('%d.%m.%y')}\n"
            f"⏰ Время: {self.selected_time}\n"
            f"💬 Комментарий: {self.comments}\n\n"
        )

        # Объединяем всё в одно сообщение
        confirmation_message = (
            f"{profile_data}"
            f"Данные для записи:\n"
            f"{admin_input_data}"
            "✅ Нажмите 'Подтвердить', чтобы сохранить запись, или '❌ Отменить', чтобы отказаться."
        )

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("✅ Подтвердить", "❌ Отменить")

        self.bot.send_message(
            message.chat.id,
            confirmation_message,
            reply_markup=markup
        )
        self.bot.register_next_step_handler(message, self.finalize_admin_booking)

    def finalize_admin_booking(self, message):
        """Сохраняет данные или отменяет процесс."""
        markup = types.ReplyKeyboardRemove()  # Убираем клавиатуру

        if message.text == "✅ Подтвердить":
            # Сохраняем данные в базе
            update_appointment(
                user_id=self.current_record_id,
                appointment_date=self.selected_date.strftime('%Y-%m-%d'),
                appointment_time=self.selected_time,
                status="Записан",
                comment=self.comments
            )

            # Уведомляем администратора
            self.bot.send_message(
                message.chat.id,
                f"✅ Пользователь с ID {self.current_record_id} успешно записан!",
                reply_markup=markup  # Убираем клавиатуру
            )

            # Уведомляем пользователя
            user_data = get_user_data_by_record_id(self.current_record_id)
            if user_data:
                self.bot.send_message(
                    user_data["telegram_user_id"],
                    f"🎉 Вы успешно записаны!\n\n"
                    f"📅 Дата: {self.selected_date.strftime('%d.%m.%y')}\n"
                    f"⏰ Время: {self.selected_time}\n"
                    f"📍 Адрес: [Укажите адрес]\n"
                    f"📞 Контакт: [Укажите телефон]\n\n"
                    "Спасибо за запись! 😊"
                )
        elif message.text == "❌ Отменить":
            self.bot.send_message(
                message.chat.id,
                "❌ Запись отменена.",
                reply_markup=markup  # Убираем клавиатуру
            )
        else:
            self.bot.send_message(
                message.chat.id,
                "❌ Некорректный выбор. Пожалуйста, нажмите '✅ Подтвердить' или '❌ Отменить'.",
                reply_markup=markup  # Убираем клавиатуру
            )

    def handle_time_selection(self, message):
        """Запрашивает выбор времени."""
        self.selected_time = message.text
        try:
            datetime.strptime(self.selected_time, '%H:%M')
            self.bot.send_message(
                message.chat.id,
                f"Вы выбрали время: {self.selected_time} ⏰. Теперь напишите комментарий (например, вид процедуры). ✍️"
            )
            self.bot.register_next_step_handler(message, self.handle_comments)
        except ValueError:
            self.bot.send_message(
                message.chat.id,
                "Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ. Например: 09:00 ⏰"
            )
            self.bot.register_next_step_handler(message, self.handle_time_selection)

    def handle_comments(self, message):
        """Запрашивает комментарии и отправляет данные на подтверждение."""
        self.comments = message.text
        confirmation_message = (
            f"📩 Подтвердите данные записи:\n\n"
            f"👤 Имя: {message.from_user.first_name or 'Не указано'} {message.from_user.last_name or ''}\n"
            f"📧 Username: {message.from_user.username or 'Не указан'}\n"
            f"🆔 Telegram ID: {message.from_user.id}\n"
            f"📅 Дата: {self.selected_date.strftime('%d.%m.%y')}\n"
            f"⏰ Время: {self.selected_time}\n"
            f"💬 Комментарий: {self.comments}\n\n"
            "✅ Нажмите 'Подтвердить', чтобы сохранить запись, или 'Отменить', чтобы отказаться."
        )
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("✅ Сохранить", "✏️ Редактировать", "❌ Отменить")

        self.bot.send_message(
            message.chat.id,
            confirmation_message,
            reply_markup=markup
        )
        self.bot.register_next_step_handler(message, self.final_confirmation)

    def final_confirmation(self, message):
        """Обрабатывает финальное подтверждение записи."""
        if message.text == "✅ Подтвердить":
            # Обновляем запись в базе данных
            save_appointment(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                phone_number=None,  # Добавьте телефон, если требуется
                date=self.selected_date.strftime('%Y-%m-%d'),
                time=self.selected_time,
                comments=self.comments,
                status='Записан'
            )

            # Уведомляем администратора
            self.bot.send_message(
                id_chat_owner,
                f"✅ Запись подтверждена:\n\n"
                f"👤 Имя: {message.from_user.first_name or 'Не указано'} {message.from_user.last_name or ''}\n"
                f"📧 Username: {message.from_user.username or 'Не указан'}\n"
                f"📅 Дата: {self.selected_date.strftime('%d.%m.%y')}\n"
                f"⏰ Время: {self.selected_time}\n"
                f"💬 Комментарий: {self.comments}\n"
            )

            # Уведомляем пользователя
            self.bot.send_message(
                message.chat.id,
                f"🎉 Вы успешно записаны!\n\n"
                f"📅 Дата: {self.selected_date.strftime('%d.%m.%y')}\n"
                f"⏰ Время: {self.selected_time}\n"
                f"📍 Адрес: [Укажите адрес]\n"
                f"📞 Контакт: [Укажите телефон]\n\n"
                "Спасибо за запись! 😊"
            )

            # Возвращаем в главное меню
            self.start_handler.main_menu(message)
        elif message.text == "❌ Отменить":
            self.handle_cancel(message)
        else:
            self.bot.send_message(
                message.chat.id,
                "❌ Некорректный выбор. Нажмите '✅ Подтвердить' или '❌ Отменить'."
            )
            self.bot.register_next_step_handler(message, self.final_confirmation)

    def process_action(self, message):
        """Обрабатывает нажатие кнопок действия: Сохранить, Редактировать, Отменить."""
        action = message.text

        if action == "✅ Сохранить":
            self.handle_save(message)
        elif action == "✏️ Редактировать":
            self.handle_edit(message)
        elif action == "❌ Отменить":
            self.handle_cancel(message)

    def handle_save(self, message):
        """Сохраняет запись и отправляет уведомление админу."""
        # Сохраняем запись в базу данных
        save_appointment(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            phone_number=None,
            # Если вы хотите, чтобы администратор получал телефонный номер, его нужно будет добавить в обработку.
            date=self.selected_date.strftime('%d.%m.%y'),
            time=self.selected_time,
            comments=self.comments,
            status='Записан'
            # Можно передавать статус как 'Записан', или добавить логику статуса в зависимости от ситуации.
        )

        # Уведомление администратора о новой записи
        self.bot.send_message(
            id_chat_owner,  # Отправляем админу
            f"📩 Новая запись: \nДата: {self.selected_date.strftime('%d.%m.%y')}\nВремя: {self.selected_time}\nКомментарии: {self.comments} 📝"
        )

        self.bot.send_message(
            message.chat.id,
            "Запись успешно сохранена! ✅\n\nНовая запись:\n"
            f"Дата: {self.selected_date.strftime('%d.%m.%y')}\n"
            f"Время: {self.selected_time}\n"
            f"Комментарии: {self.comments} 📝"
        )

        # Убираем клавиатуру с кнопками
        self.bot.send_message(
            message.chat.id,
            "Запись сохранена. Возвращаемся в главное меню... 🏠",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Возвращаем в главное меню
        self.start_handler.main_menu(message)  # Вызываем main_menu через start_handler

    def handle_cancel(self, message):
        """Отменяет запись."""
        self.bot.send_message(
            message.chat.id,
            "Запись отменена ❌"
        )

        # Убираем клавиатуру с кнопками
        self.bot.send_message(
            message.chat.id,
            "Отмена завершена. Возвращаемся в главное меню... 🏠",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Возвращаем в главное меню
        self.start_handler.main_menu(message)  # Вызываем main_menu через start_handler

    def handle_edit(self, message):
        """Редактирует выбранное поле: дату, время или комментарий."""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📅 Изменить дату", "⏰ Изменить время", "💬 Изменить комментарий")
        self.bot.send_message(
            message.chat.id,
            "Что вы хотите отредактировать?",
            reply_markup=markup
        )
        self.bot.register_next_step_handler(message, self.process_edit_choice)

    def process_edit_choice(self, message):
        """Обрабатывает выбор того, что редактировать."""
        if message.text == "📅 Изменить дату":
            self.bot.send_message(
                message.chat.id,
                "Введите новую дату (формат: ДД.ММ.ГГ) 🗓️"
            )
            self.bot.register_next_step_handler(message, self.handle_date_selection)

        elif message.text == "⏰ Изменить время":
            self.bot.send_message(
                message.chat.id,
                "Введите новое время (формат: ЧЧ:ММ) ⏰"
            )
            self.bot.register_next_step_handler(message, self.handle_time_selection)

        elif message.text == "💬 Изменить комментарий":
            self.bot.send_message(
                message.chat.id,
                "Введите новый комментарий 📝"
            )
            self.bot.register_next_step_handler(message, self.handle_comments)
