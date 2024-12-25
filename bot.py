from telebot import TeleBot

import config
from handlers.StartHandler import StartHandler
from handlers.BookingHandler import BookingHandler
from handlers.UserRequestHandler import UserRequestHandler
# from handlers.AdminNotificationHandler import AdminNotificationHandler
# from handlers.ChatHandler import ChatHandler

# Создаем объект бота с использованием токена из config.py
bot = TeleBot(config.TELEBOT_TOKEN)

# Используем идентификатор администратора из config.py
ADMIN_CHAT_ID = int(config.id_chat_owner)  # Преобразуем в int, если это строка

# Создание экземпляров обработчиков
start_handler = StartHandler(bot)
booking_handler = BookingHandler(bot, start_handler)  # Передаем start_handler
user_request_handler = UserRequestHandler(bot, ADMIN_CHAT_ID)
# admin_notification_handler = AdminNotificationHandler(bot)
# chat_handler = ChatHandler(bot)



# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Обрабатывает команду /start, чтобы отобразить главное меню."""
    start_handler.main_menu(message)

# Обработчик для записи клиента
@bot.message_handler(func=lambda message: message.text == "📝 Записать клиента")
def handle_booking(message):
    """Начинает процесс записи клиента."""
    booking_handler.start_booking(message)

# Обработчик для сохранения, редактирования или отмены записи
@bot.message_handler(func=lambda message: message.text in ["✅ Сохранить", "✏️ Редактировать", "❌ Отменить"])
def handle_confirmation(message):
    """Обрабатывает подтверждения от пользователя."""
    booking_handler.process_action(message)

@bot.message_handler(func=lambda message: message.text == "📅 Узнать о свободных слотах")
def handle_user_request(message):
    """Обрабатывает запрос от пользователя."""
    user_request_handler.start_request(message)

@bot.message_handler(content_types=['contact'])
def handle_contact_message(message):
    """Передает контактное сообщение в UserRequestHandler."""
    user_request_handler.handle_contact(message)

# @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
# def handle_admin_actions(call):
#     """Обрабатывает действия администратора."""
#     admin_notification_handler.process_admin_action(call)
#
# @bot.message_handler(func=lambda message: chat_handler.is_chat_active(message))
# def handle_chat_messages(message):
#     """Обрабатывает сообщения в личной переписке между администратором и пользователем."""
#     chat_handler.process_message(message)




# Запуск бота
bot.polling(none_stop=True)

if __name__ == "__main__":
    bot.polling(none_stop=True)