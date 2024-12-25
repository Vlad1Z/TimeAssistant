from telebot import types
from datetime import datetime
from db import save_appointment


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

    def handle_date_selection(self, message):
        """Обрабатывает выбор даты."""
        try:
            self.selected_date = datetime.strptime(message.text, '%d.%m.%y').date()
            if self.selected_date < datetime.today().date():
                raise ValueError("Дата не может быть в прошлом.")
            self.bot.send_message(
                message.chat.id,
                f"Вы выбрали дату: {self.selected_date.strftime('%d.%m.%y')} 🗓️. Теперь укажите время ⏰."
            )
            self.bot.register_next_step_handler(message, self.handle_time_selection)
        except ValueError as e:
            error_message = str(e) if str(e) else "Неверный формат даты. Пожалуйста, введите дату в формате ДД.ММ.ГГ."
            self.bot.send_message(
                message.chat.id,
                error_message + " ❌"
            )
            self.bot.register_next_step_handler(message, self.handle_date_selection)

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
        """Запрашивает комментарии, такие как вид процедуры."""
        self.comments = message.text
        confirmation_message = (
            f"📅 Дата: {self.selected_date.strftime('%d.%m.%y')}\n"
            f"⏰ Время: {self.selected_time}\n"
            f"💬 Комментарии: {self.comments}\n\n"
            "Выберите действие:"
        )
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("✅ Сохранить", "✏️ Редактировать", "❌ Отменить")

        self.bot.send_message(
            message.chat.id,
            confirmation_message,
            reply_markup=markup
        )

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
        """Сохраняет запись."""
        self.bot.send_message(
            message.chat.id,
            "Запись успешно сохранена! ✅\n\nНовая запись:\n"
            f"Дата: {self.selected_date.strftime('%d.%m.%y')}\n"
            f"Время: {self.selected_time}\n"
            f"Комментарии: {self.comments} 📝"
        )

        # Уведомление администратора о новой записи
        self.bot.send_message(
            message.chat.id,
            f"📩 Новая запись: \nДата: {self.selected_date.strftime('%d.%m.%y')}\nВремя: {self.selected_time}\nКомментарии: {self.comments} 📝"
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
