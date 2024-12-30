import logging
from telebot import TeleBot
from telebot import types
import config
from handlers.StartHandler import StartHandler
from handlers.BookingHandler import BookingHandler
from handlers.UserRequestHandler import UserRequestHandler
from handlers.ProceduresHandler import ProceduresHandler
from handlers.UserStatisticsHandler import UserStatisticsHandler
from handlers.RecordsHandler import RecordsHandler
from db import save_user_visit, get_user_data_by_record_id, update_appointment, log_user_action, get_records_from_today


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
user_statistics_handler = UserStatisticsHandler(bot)
records_handler = RecordsHandler(bot)



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
    log_user_action(user_id=call.message.chat.id, username=call.from_user.username, action_type="inline_button",
                    action_details=f"Нажата кнопка: {call.data}")
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
    """Обрабатывает нажатие инлайн-кнопок."""
    bot.answer_callback_query(call.id)  # Убираем индикатор загрузки

    if call.data == "confirm_booking":
        # Проверяем record_id
        print(f"Текущий record_id: {booking_handler.current_record_id}")

        # Получаем данные пользователя из базы
        user_data = get_user_data_by_record_id(booking_handler.current_record_id)

        if not user_data:
            bot.send_message(
                call.message.chat.id,
                "❌ Ошибка: данные пользователя не найдены."
            )
            print(f"Пользователь с record_id {booking_handler.current_record_id} не найден.")
            return

        # Проверяем наличие message_id
        message_id_request = user_data.get("message_id")
        print(f"Полученный message_id: {message_id_request}")

        if message_id_request:
            try:
                bot.delete_message(call.message.chat.id, message_id_request)
                print(f"Сообщение с message_id {message_id_request} успешно удалено.")
            except Exception as e:
                print(f"Не удалось удалить сообщение с заявкой: {e}")
        else:
            print("Ошибка: message_id отсутствует в базе.")

        # Обновляем запись в базе данных
        update_appointment(
            user_id=booking_handler.current_record_id,  # ID записи
            appointment_date=booking_handler.selected_date.strftime('%Y-%m-%d'),
            appointment_time=booking_handler.selected_time,
            status="Записан",
            comment=booking_handler.comments
        )

        # Формируем сообщение с полной информацией о клиенте
        updated_message = (
            "✅ Запись успешно подтверждена!\n\n"
            f"👤 Имя: {user_data['first_name']} {user_data['last_name']}\n"
            f"📱 Телефон: {user_data['phone_number']}\n"
            f"📧 Username: @{user_data['username']}\n"
            f"🆔 ID клиента: <code>{user_data['telegram_user_id']}</code>\n\n"
            f"📅 Дата: {booking_handler.selected_date.strftime('%d.%m.%y')}\n"
            f"⏰ Время: {booking_handler.selected_time}\n"
            f"💬 Комментарий: {booking_handler.comments}"
        )

        # Создаём кнопку "Написать"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "Написать", url=f"tg://user?id={user_data['telegram_user_id']}"
            )
        )

        # Редактируем текущее сообщение с кнопками
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=updated_message,
            reply_markup=markup,
            parse_mode="HTML"
        )

        # Уведомляем клиента о записи
        bot.send_message(
            user_data["telegram_user_id"],
            f"🎉 Вы успешно записаны!\n\n"
            f"📅 Дата: {booking_handler.selected_date.strftime('%d.%m.%y')}\n"
            f"⏰ Время: {booking_handler.selected_time}\n"
            f"📍 Адрес: [Укажите адрес]\n"
            f"📞 Контакт: [Укажите телефон]\n"
            f"💬 Комментарий: {booking_handler.comments}\n\n"
            "Спасибо за запись! 😊",
            parse_mode="HTML"
        )





    elif call.data == "cancel_booking":

        # Получаем данные пользователя из базы

        user_data = get_user_data_by_record_id(booking_handler.current_record_id)

        if not user_data:
            bot.send_message(

                call.message.chat.id,

                "❌ Ошибка: данные пользователя не найдены."

            )

            print(f"Пользователь с record_id {booking_handler.current_record_id} не найден.")

            return

        # Проверяем наличие message_id

        message_id_request = user_data.get("message_id")

        print(f"Полученный message_id: {message_id_request}")

        if message_id_request:

            try:
                # Удаляем сообщение, используя chat_id администратора
                bot.delete_message(call.message.chat.id, message_id_request)
                print(f"Сообщение с message_id {message_id_request} успешно удалено.")
            except Exception as e:
                print(f"Не удалось удалить сообщение с заявкой: {e}")
        else:
            print("Ошибка: message_id отсутствует в базе.")

        # Обновляем запись в базе данных
        update_appointment(
            user_id=booking_handler.current_record_id,  # ID записи
            appointment_date=None,
            appointment_time=None,
            status="Отклонена",
            comment=None
        )

        # Формируем сообщение с информацией об отклонении
        decline_message = (
            f"❌ Запись отклонена! (Заявка №{booking_handler.current_record_id})\n\n"
            f"👤 Имя: {user_data['first_name']} {user_data['last_name']}\n"
            f"📱 Телефон: {user_data['phone_number']}\n"
            f"📧 Username: @{user_data['username']}\n"
            f"🆔 ID клиента: <code>{user_data['telegram_user_id']}</code>\n"
        )

        # Отправляем сообщение о статусе
        bot.send_message(
            chat_id=call.message.chat.id,
            text=decline_message,
            parse_mode="HTML"
        )
        print(f"Статус записи {booking_handler.current_record_id} обновлён на 'Отклонена'.")


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
    log_user_action(user_id=message.chat.id, username=message.from_user.username, action_type="menu_click",
                    action_details="Узнать о свободных слотах")
    user_request_handler.start_request(message)

# Обработчик для получения контакта
@bot.message_handler(content_types=['contact'])
def handle_contact_message(message):
    """Передает контактное сообщение в UserRequestHandler."""
    # Логируем полученные данные для отладки
    print("Contact received:", message.contact)

    # Передаем данные в UserRequestHandler
    user_request_handler.handle_contact(message)

# Обработчик кнопки "Виды процедур"
@bot.message_handler(func=lambda message: message.text == "💆‍♀️ Виды процедур")
def handle_procedures(message):
    """Обрабатывает нажатие на кнопку 'Виды процедур'."""
    log_user_action(user_id=message.chat.id, username=message.from_user.username, action_type="menu_click",
                    action_details="Виды процедур")
    procedures_handler.show_procedures(message)

# Обработчик кнопки "Записаться" в описании процедур
@bot.callback_query_handler(func=lambda call: call.data == "book_procedure")
def handle_procedure_booking(call):
    """Обрабатывает нажатие на 'Записаться' в видах процедур."""
    procedures_handler.handle_booking_procedure(call)

@bot.callback_query_handler(func=lambda call: call.data == "get_contact")
def handle_get_contact(call):
    """Обрабатывает нажатие на 'Узнать подробнее'."""
    procedures_handler.handle_booking_procedure(call)

@bot.message_handler(func=lambda message: message.text == "👥 Посмотреть пользователей")
def handle_view_users(message):
    """Обрабатывает нажатие на 'Посмотреть пользователей'."""
    bot.delete_message(message.chat.id, message.message_id)
    user_statistics_handler.show_statistics(message)

@bot.callback_query_handler(func=lambda call: call.data in ["unique_users", "repeat_visits", "inactive_users"])
def handle_statistics_detail(call):
    """Обрабатывает нажатие на ссылки статистики."""
    bot.answer_callback_query(call.id)  # Убираем индикатор загрузки
    user_statistics_handler.handle_detailed_statistics(call)


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    log_user_action(user_id=call.message.chat.id, username=call.from_user.username, action_type="button_click", action_details=call.data)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_stats")
def handle_back_to_stats(call):
    """Возвращает в главное меню статистики."""
    user_statistics_handler.show_statistics(call.message)

@bot.message_handler(func=lambda message: message.text == "📋 Отобразить записи")
def handle_show_records(message):
    """Обрабатывает нажатие на 'Отобразить записи'."""
    bot.delete_message(message.chat.id, message.message_id)  # Удаляем сообщение пользователя
    records_handler.show_records(message)


# Запуск бота
if __name__ == "__main__":
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logging.error(f"Error occurred: {e}")
