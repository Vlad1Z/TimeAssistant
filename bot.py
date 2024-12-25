import logging
from telebot import TeleBot
import config
from handlers.StartHandler import StartHandler
from handlers.BookingHandler import BookingHandler
from handlers.UserRequestHandler import UserRequestHandler

# Настроим логирование
logging.basicConfig(level=logging.INFO)
logging.info("Bot is starting...")

# Создаем объект бота с использованием токена из config.py
bot = TeleBot(config.TELEBOT_TOKEN)

# Используем идентификатор администратора из config.py
ADMIN_CHAT_ID = int(config.id_chat_owner)

# Создание экземпляров обработчиков
start_handler = StartHandler(bot)
booking_handler = BookingHandler(bot, start_handler)
user_request_handler = UserRequestHandler(bot, ADMIN_CHAT_ID)

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

# Обработчик для запроса доступных слотов
@bot.message_handler(func=lambda message: message.text == "📅 Узнать о свободных слотах")
def handle_user_request(message):
    """Обрабатывает запрос от пользователя."""
    user_request_handler.start_request(message)

# Обработчик для получения контакта
@bot.message_handler(content_types=['contact'])
def handle_contact_message(message):
    """Передает контактное сообщение в UserRequestHandler."""
    user_request_handler.handle_contact(message)

# Запуск бота
if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Error occurred: {e}")
