from telebot import TeleBot, types
from config import TELEBOT_TOKEN, id_chat_owner
from handlers.StartHandler import StartHandler
from handlers.BookingHandler import BookingHandler
from CalendarHandler.MainMenuHandler import MainMenuHandler
from CalendarHandler.UnlockTimeHandler import UnlockTimeHandler
from CalendarHandler.BookingListHandler import BookingListHandler

bot = TeleBot(TELEBOT_TOKEN)

# Экземпляры обработчиков
start_handler = StartHandler(bot)
booking_handler = BookingHandler(bot)
main_menu_handler = MainMenuHandler(bot)
unlock_handler = UnlockTimeHandler(bot, booking_handler)
bookings_handler = BookingListHandler(bot, booking_handler)

# Функция для регистрации обработчиков
def register_handlers():
    """Регистрирует обработчики сообщений для различных команд и текстовых сообщений."""
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        """Обрабатывает команду /start, отправляя пользователю приветственное сообщение
            и отображая главное меню с параметром is_welcome=True."""
        start_handler.handle(message, is_welcome=True)

    @bot.message_handler(commands=['help'])
    def handle_help(message):
        """Обрабатывает команду /help, отправляя пользователю справочную информацию."""
        start_handler.send_help_message(message)

    @bot.message_handler(func=lambda message: message.text in ['📅 Записаться', '🌐 Социальные сети', '💆‍♀️ Наши услуги', '🕒 Настройки расписания'])
    def handle_main_menu(message):
        """Обрабатывает запросы из главного меню."""
        if message.text == '📅 Записаться':
            booking_handler.handle(message)
        elif message.text == '🌐 Социальные сети':
            # Логика обработки выбора социальных сетей
            bot.send_message(message.chat.id, "Наши социальные сети: ...")
        elif message.text == '💆‍♀️ Наши услуги':
            # Логика обработки выбора услуг
            bot.send_message(message.chat.id, "Наши услуги: ...")
        elif message.text == '🕒 Настройки расписания' and str(message.chat.id) == id_chat_owner:
            main_menu_handler.handle_calendar(message)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('type_'))
    def handle_type(call):
        booking_type = call.data.split('_')[1]
        booking_handler.show_available_slots(call, booking_type)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('date_'))
    def handle_date(call):
        date = call.data.split('_')[1]
        booking_handler.show_times(call, date)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('time_'))
    def handle_time(call):
        _, date, time = call.data.split('_')
        booking_handler.book_time(call, date, time)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('unlock_date_'))
    def handle_unlock_date(call):
        print(f"handle_unlock_date called with data: {call.data}")
        date = call.data.split('_')[2]
        unlock_handler.show_unlock_times(call, date)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('unlock_time_'))
    def handle_unlock_time_slots(call):
        print(f"handle_unlock_time_slots called with data: {call.data}")
        parts = call.data.split('_')
        date = parts[2]
        time = parts[3]
        unlock_handler.unlock_time(call, date, time)

    @bot.callback_query_handler(func=lambda call: call.data == 'unlock_time')
    def handle_unlock_time(call):
        print("handle_unlock_time called")
        unlock_handler.show_unlock_dates(call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('done_unlock_'))
    def handle_done_unlock(call):
        print(f"handle_done_unlock called with data: {call.data}")
        date = call.data.split('_')[2]
        unlock_handler.confirm_unlock(call, date)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('back_to_unlock_dates'))
    def handle_back_to_unlock_dates(call):
        print(f"handle_back_to_unlock_dates called with data: {call.data}")
        date = call.data.split('_')[2]
        unlock_handler.show_unlock_dates(call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('back_to_calendar'))
    def handle_back_to_calendar(call):
        print("handle_back_to_calendar called")
        main_menu_handler.handle_calendar(call.message)

    # Обработчик команды для очистки расписания
    @bot.callback_query_handler(func=lambda call: call.data == 'clear_schedule')
    def handle_clear_schedule(call):
        print("handle_clear_schedule called")
        unlock_handler.clear_schedule(call)

    @bot.callback_query_handler(func=lambda call: call.data == 'back_to_main')
    def handle_back_to_main(call):
        """Обрабатывает нажатие на кнопку 'Назад' в меню 'Настройки расписания'."""
        start_handler.handle(call.message, is_welcome=False)

    @bot.callback_query_handler(func=lambda call: call.data == 'handle_calendar')
    def handle_calendar(call):
        main_menu_handler.handle_calendar(call.message)
        markup = types.InlineKeyboardMarkup()
        unlock_button = types.InlineKeyboardButton(text="Освободить время под записи", callback_data='unlock_time')
        get_bookings_button = types.InlineKeyboardButton(text="Прислать список записей", callback_data='get_bookings')
        clear_schedule_button = types.InlineKeyboardButton(text="Очистить расписание", callback_data='clear_schedule')
        back_button = types.InlineKeyboardButton(text="Назад", callback_data='back_to_main')
        markup.add(unlock_button)
        markup.add(get_bookings_button)
        markup.add(clear_schedule_button)
        markup.add(back_button)
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выберите действие:", reply_markup=markup)


register_handlers()

bot.polling(none_stop=True)
