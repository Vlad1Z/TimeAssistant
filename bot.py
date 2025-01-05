import logging
from telebot import TeleBot
from telebot import types
import config
from handlers.StartHandler import StartHandler
from handlers.BookingHandler import BookingHandler
from handlers.UserRequestHandler import UserRequestHandler
from handlers.ProceduresHandler import ProceduresHandler
from handlers.UserStatisticsHandler import (
    UniqueUsersStatisticsHandler,
    RepeatVisitsStatisticsHandler,
    InactiveUsersStatisticsHandler,
    VisitedSectionsStatisticsHandler,
    BaseStatisticsHandler
)
from handlers.RecordsHandler import RecordsHandler
from handlers.SocialMediaHandler import SocialMediaHandler
from db import save_user_visit, get_user_data_by_record_id, update_appointment, get_records_from_today
from handlers.Logger import log_action


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
procedures_handler = ProceduresHandler(bot, ADMIN_CHAT_ID)
records_handler = RecordsHandler(bot)
social_media_handler = SocialMediaHandler(bot)

# из файла UserStatisticsHandler.py
unique_users_handler = UniqueUsersStatisticsHandler(bot)
repeat_visits_handler = RepeatVisitsStatisticsHandler(bot)
inactive_users_handler = InactiveUsersStatisticsHandler(bot)
visited_sections_handler = VisitedSectionsStatisticsHandler(bot)



# Обработчик команды /start
@bot.message_handler(commands=['start'])
@log_action(action_type="start_command", action_details="Запуст бота")
def handle_start(message):
    """Обрабатывает команду /start (при первом взаимодействии с ботом)."""
    start_handler.main_menu(message)

@bot.message_handler(func=lambda message: message.text == "🙏 Спасибо, вернуться позже")
@log_action(action_type="menu_click", action_details="Спасибо, вернуться позже")
def handle_exit(message):
    """Обрабатывает нажатие на кнопку 'Спасибо, вернуться позже'."""
    # Создаем клавиатуру с одной кнопкой "Запустить"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton("🚀 Запустить")
    markup.add(button)

    # Отправляем сообщение пользователю
    bot.send_message(
        message.chat.id,
        "💖 Спасибо, что воспользовались нашим ботом! Мы всегда рады вам помочь. Хорошего дня! 😊\n\n"
        "🚀 Когда будете готовы вернуться, нажмите 'Запустить'.",
        reply_markup=markup  # Устанавливаем новую клавиатуру
    )

@bot.message_handler(func=lambda message: message.text == "🚀 Запустить")
@log_action(action_type="button_click", action_details="Возвращение в бота")
def handle_restart(message):
    start_handler.main_menu(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("record_"))
def handle_admin_booking(call):
    # Ваш код обработки инлайн-кнопки
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

@bot.callback_query_handler(func=lambda call: call.data in ["confirm_booking", "cancel_booking"])
def handle_booking_confirmation(call):
    """Обрабатывает нажатие инлайн-кнопок подтверждения или отклонения заявки."""
    bot.answer_callback_query(call.id)  # Убираем индикатор загрузки

    # Проверяем, к какому действию относится нажатая кнопка
    action = "confirm" if call.data == "confirm_booking" else "cancel"
    record_id = booking_handler.current_record_id

    # Получаем данные пользователя из базы
    user_data = get_user_data_by_record_id(record_id)

    if not user_data:
        bot.send_message(
            call.message.chat.id,
            "❌ Ошибка: данные пользователя не найдены."
        )
        print(f"Пользователь с record_id {record_id} не найден.")
        return

    # Проверяем наличие message_id заявки
    message_id_request = user_data.get("message_id")
    if message_id_request:
        try:
            # Удаляем сообщение с заявкой
            bot.delete_message(chat_id=call.message.chat.id, message_id=message_id_request)
            print(f"Сообщение с message_id {message_id_request} успешно удалено.")
        except Exception as e:
            print(f"Не удалось удалить сообщение с заявкой: {e}")

    # Формируем текст для редактирования сообщения подтверждения/отклонения
    if action == "confirm":
        # Обновляем запись в базе данных
        update_appointment(
            user_id=record_id,
            appointment_date=booking_handler.selected_date.strftime('%Y-%m-%d'),
            appointment_time=booking_handler.selected_time,
            status="Записан",
            comment=booking_handler.comments
        )
        updated_message = (
            "✅ Запись успешно подтверждена!\n\n"
            f"👤 Имя: {user_data.get('first_name', '')} {user_data.get('last_name', '')}\n"
            f"📱 Телефон: {user_data.get('phone_number', 'Не указан')}\n"
            f"📧 Username: @{user_data.get('username', 'Не указан')}\n"
            f"🆔 ID клиента: <code>{user_data.get('telegram_user_id', 'Не указан')}</code>\n\n"
            f"📅 Дата: {booking_handler.selected_date.strftime('%d.%m.%y')}\n"
            f"⏰ Время: {booking_handler.selected_time}\n"
            f"💬 Комментарий: {booking_handler.comments if booking_handler.comments else 'Нет комментариев'}"
        )

    elif action == "cancel":
        # Обновляем запись в базе данных
        update_appointment(
            user_id=record_id,
            appointment_date=None,
            appointment_time=None,
            status="Отклонена",
            comment=None
        )
        updated_message = (
            f"❌ Заявка №{record_id} отклонена!\n\n"
            f"👤 Имя: {user_data['first_name']} {user_data['last_name']}\n"
            f"📱 Телефон: {user_data['phone_number']}\n"
            f"📧 Username: @{user_data['username']}\n"
            f"🆔 ID клиента: <code>{user_data['telegram_user_id']}</code>"
        )

    # Редактируем текущее сообщение
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=updated_message,
            parse_mode="HTML"
        )
        print(f"Сообщение о заявке №{record_id} успешно обновлено.")
    except Exception as e:
        print(f"Ошибка при редактировании сообщения: {e}")


def process_cancel_booking(record_id, call=None):
    """
    Обрабатывает отклонение заявки.
    """
    # Получаем данные пользователя по record_id
    user_data = get_user_data_by_record_id(record_id)

    if not user_data:
        if call:
            bot.send_message(call.message.chat.id, "❌ Ошибка: данные пользователя не найдены.")
        return

    # Обновляем запись в базе данных
    update_appointment(
        user_id=record_id,
        appointment_date=None,
        appointment_time=None,
        status="Отклонена",
        comment=None
    )

    # Формируем текст для обновления
    updated_message = (
        f"❌ Запись отклонена! (Заявка №{record_id})\n\n"
        f"👤 Имя: {user_data['first_name']} {user_data['last_name']}\n"
        f"📱 Телефон: {user_data['phone_number']}\n"
        f"📧 Username: @{user_data['username']}\n"
        f"🆔 ID клиента: <code>{user_data['telegram_user_id']}</code>\n"
    )

    # Редактируем текущее сообщение
    try:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=updated_message,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Ошибка при редактировании сообщения: {e}")



@bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
def handle_cancel_booking(call):
    """Обрабатывает нажатие на кнопку 'Отклонить'."""
    try:
        # Извлекаем record_id
        record_id = int(call.data.split("_")[1])

        # Вызываем метод process_cancel_booking с правильным аргументом
        process_cancel_booking(record_id=record_id, call=call)
    except Exception as e:
        print(f"Ошибка при обработке отмены заявки: {e}")



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
@log_action(action_type="menu_click", action_details="Узнать о свободных слотах")
def handle_user_request(message):
    """Обрабатывает запрос от пользователя."""
    user_request_handler.start_request(message)

# Обработчик для получения контакта
@bot.message_handler(content_types=['contact'])
@log_action(action_type="button_click", action_details="Отправить номер телефона")
def handle_contact_message(message):
    """Передает контактное сообщение в UserRequestHandler."""
    # Логируем полученные данные для отладки
    print("Contact received:", message.contact)

    # Передаем данные в UserRequestHandler
    user_request_handler.handle_contact(message)

# Обработчик кнопки "Виды процедур"
@bot.message_handler(func=lambda message: message.text == "✨ Виды процедур")
@log_action(action_type="menu_click", action_details="Виды процедур")
def handle_procedures(message):
    """Обрабатывает нажатие на кнопку 'Виды процедур'."""
    procedures_handler.show_procedures(message)

# Обработчик кнопки "Записаться" в описании процедур
@bot.callback_query_handler(func=lambda call: call.data == "book_procedure")
def handle_procedure_booking(call):
    """Обрабатывает нажатие на 'Записаться' в видах процедур."""
    procedures_handler.handle_booking_procedure(call)

@bot.callback_query_handler(func=lambda call: call.data == "get_contact")
@log_action(action_type="button_click", action_details="Узнать подробнее")
def handle_get_contact(call):
    """Обрабатывает нажатие на 'Узнать подробнее'."""
    procedures_handler.handle_booking_procedure(call)

@bot.message_handler(func=lambda message: message.text == "📋 Отобразить записи")
def handle_show_records(message):
    """Обрабатывает нажатие на 'Отобразить записи'."""
    bot.delete_message(message.chat.id, message.message_id)  # Удаляем сообщение пользователя
    records_handler.show_records(message)

@bot.message_handler(func=lambda message: message.text == "🌐 Другие соц сети")
@log_action(action_type="button_click", action_details="Другие соц сети")
def handle_social_media(message):
    """Обрабатывает нажатие на кнопку 'Другие соц сети'."""
    social_media_handler.show_social_media(message)









@bot.message_handler(func=lambda message: message.text == "👥 Посмотреть пользователей")
def handle_view_users(message):
    """Обрабатывает нажатие на 'Посмотреть пользователей'."""
    bot.delete_message(message.chat.id, message.message_id)
    # Общий метод для отображения статистики
    base_statistics_handler = BaseStatisticsHandler(bot)
    base_statistics_handler.show_statistics(message)

@bot.callback_query_handler(func=lambda call: call.data == "unique_users")
def handle_unique_users(call):
    """Обрабатывает запрос на уникальных пользователей."""
    bot.answer_callback_query(call.id)
    unique_users_handler.pending_section[call.message.chat.id] = "unique_users"
    unique_users_handler.request_date_range_unique_user(call)

@bot.callback_query_handler(func=lambda call: call.data == "repeat_visits")
def handle_repeat_visits(call):
    """Обрабатывает запрос на повторные посещения."""
    bot.answer_callback_query(call.id)
    repeat_visits_handler.handle_statistics(call)

@bot.callback_query_handler(func=lambda call: call.data == "inactive_users")
def handle_inactive_users(call):
    """Обрабатывает запрос на неактивных пользователей."""
    bot.answer_callback_query(call.id)
    inactive_users_handler.pending_section[call.message.chat.id] = "inactive_users"
    inactive_users_handler.request_date_range_inactive_users(call)

@bot.callback_query_handler(func=lambda call: call.data == "section_stats")
def handle_visited_sections(call):
    """Обрабатывает запрос на посещённые разделы."""
    bot.answer_callback_query(call.id)
    visited_sections_handler.handle_statistics(call)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def handle_back_to_menu(call):
    """Возвращает в главное меню статистики."""
    base_statistics_handler = BaseStatisticsHandler(bot)
    base_statistics_handler.handle_back_to_menu(call)

@bot.message_handler(content_types=['text'])
def handle_text_message(message):
    """Обрабатывает текстовые сообщения."""
    # Проверяем, ожидает ли бот ввода даты для уникальных пользователей
    if message.chat.id in inactive_users_handler.pending_section:
        # Сначала проверяем неактивных пользователей
        inactive_users_handler.process_date_input_inactive_users(message)
    elif message.chat.id in unique_users_handler.pending_section:
        # Затем уникальных пользователей
        unique_users_handler.process_date_input_unique_users(message)
    else:
        bot.send_message(
            message.chat.id,
            "❌ Неизвестная команда. Пожалуйста, выберите раздел из меню.",
            parse_mode="HTML"
        )



# Запуск бота
if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Error occurred: {e}")
