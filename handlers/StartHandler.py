from telebot import types
from config import id_chat_owner
from db import log_user_action


class StartHandler:
    def __init__(self, bot):
        self.bot = bot

    def main_menu(self, message):
        """Отображает главное меню для админа или пользователя.
    Включает проверку на роль пользователя (администратор или клиент)
    и отображает соответствующие кнопки и приветственное сообщение."""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        # Проверка, кто отправил команду
        if str(message.chat.id) == id_chat_owner:
            # Меню для админа
            markup.row("📝 Записать", "📋 Отобразить записи")
            markup.add("👥 Посмотреть пользователей")
            welcome_text = (
                "👨‍💼 Здравствуйте, Администратор!\n\n"
                "Выберите одну из опций ниже, чтобы продолжить."
            )
        else:
            # Меню для пользователя
            markup.row("✨ Виды процедур", "🌐 Другие соц сети")
            markup.add("📅 Узнать о свободных слотах")
            welcome_text = (
                "🎉 Добро пожаловать! Я ваш личный помощник. 👋\n\n"
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

    def show_main_menu_buttons(self, chat_id, message_id=None):
        """Обновляет кнопки главного меню."""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

        if str(chat_id) == id_chat_owner:
            markup.add("📝 Записать")
            markup.add("📋 Отобразить записи")
            markup.add("👥 Посмотреть пользователей")
        else:
            markup.row("✨ Виды процедур", "🌐 Другие соц сети")
            markup.add("📅 Узнать о свободных слотах")
            markup.add("🙏 Спасибо, вернуться позже")  # Добавляем новую кнопку

        if message_id:
            # Редактируем только клавиатуру, если передан message_id
            self.bot.edit_message_reply_markup(chat_id, message_id, reply_markup=markup)
        else:
            # Если нет message_id, просто отправляем сообщение с клавиатурой
            self.bot.send_message(chat_id, "👇 Выберите действие из меню:", reply_markup=markup)

    def show_start_button(self, chat_id):
        """Отображает кнопку 'Запустить' для пользователя, чтобы начать взаимодействие с ботом.
            Используется, если меню пользователя было ранее скрыто или удалено."""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("🚀 Запустить")
        self.bot.send_message(chat_id, "Добро пожаловать! Нажмите 'Запустить', чтобы начать. 🚀", reply_markup=markup)


