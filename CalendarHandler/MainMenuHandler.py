import datetime
from telebot import types
from config import id_chat_owner

class MainMenuHandler:
    def __init__(self, bot):
        self.bot = bot

    def handle_calendar(self, message):
        """
        Отображает меню с действиями для владельца бота, связанными с управлением календарем.
        Включает кнопки для разблокировки времени под записи, получения списка записей и возврата в главное меню.

        :param message: Сообщение от пользователя, которое передается для создания интерфейса меню.
        """
        print("handle_calendar called")
        markup = types.InlineKeyboardMarkup()
        unlock_button = types.InlineKeyboardButton(text="Освободить время под записи", callback_data='unlock_time')
        get_bookings_button = types.InlineKeyboardButton(text="Прислать список записей", callback_data='get_bookings')
        back_button = types.InlineKeyboardButton(text="Назад", callback_data='back_to_main')
        markup.add(unlock_button)
        markup.add(get_bookings_button)
        markup.add(back_button)
        self.bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
