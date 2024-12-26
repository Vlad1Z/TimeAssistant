import logging
from telebot import TeleBot
import config
from handlers.StartHandler import StartHandler
from handlers.BookingHandler import BookingHandler
from handlers.UserRequestHandler import UserRequestHandler
from db import save_user_visit

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
    """Обрабатывает команду /start (при первом взаимодействии с ботом)."""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Логируем информацию о пользователе
    save_user_visit(user_id, username, first_name, last_name)

    start_handler.main_menu(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("record_"))
def handle_admin_booking(call):
    """Обрабатывает нажатие на кнопку 'Записать'."""
    try:
        record_id = int(call.data.split("_")[-1])  # Получаем ID записи из callback_data
        print(f"Callback data received: {call.data}, record ID: {record_id}")

        # Проверяем существование записи в базе данных
        from db import check_appointment_exists
        if not check_appointment_exists(record_id):
            bot.answer_callback_query(call.id, "❌ Запись не найдена. Возможно, она была удалена.")
            return

        bot.answer_callback_query(call.id, "Начинаем процесс записи клиента!")
        booking_handler.start_admin_booking(call, record_id)  # Передаём управление в BookingHandler
    except Exception as e:
        print(f"Ошибка в обработчике callback_query: {e}")



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
    # Логируем полученные данные для отладки
    print("Contact received:", message.contact)

    # Передаем данные в UserRequestHandler
    user_request_handler.handle_contact(message)


# Запуск бота
if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Error occurred: {e}")
