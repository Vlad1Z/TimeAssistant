import datetime
from telebot import types
from config import id_chat_owner
from utils import notify_owner

class CalendarHandler:
    """
    Класс CalendarHandler управляет процессом разблокировки времени и получения списка записей.
    """
    def __init__(self, bot, booking_handler):
        """Инициализирует обработчик с экземпляром бота и ссылкой на обработчик записей.
        :param bot: Экземпляр телеграм-бота.
        :param booking_handler: Обработчик записей для взаимодействия с расписанием.
        """
        self.bot = bot
        self.booking_handler = booking_handler
        self.selected_times = {}  # Словарь для хранения выбранных временных слотов

    def handle_calendar(self, message):
        """
        Отображает меню календаря для владельца.
        :param message: Сообщение от пользователя.
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

    def show_unlock_dates(self, call):
        """Отображает даты для разблокировки слотов на следующие три недели."""
        print("show_unlock_dates called")
        markup = types.InlineKeyboardMarkup()
        start_date = datetime.date.today()
        for week in range(3):  # Генерируем расписание на три недели
            for day in range(7):
                date = start_date + datetime.timedelta(days=day + week * 7)
                formatted_date = date.strftime("%d.%m %A")
                date_button = types.InlineKeyboardButton(text=formatted_date, callback_data=f'unlock_date_{date}')
                markup.add(date_button)
        back_button = types.InlineKeyboardButton(text="Назад", callback_data='back_to_calendar')
        markup.add(back_button)
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   text="Выберите дату для разблокировки слотов:", reply_markup=markup)

    def show_unlock_times(self, call, date):
        """Отображает временные слоты для разблокировки."""
        print(f"show_unlock_times called with date: {date}")
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        if date not in self.selected_times:
            self.selected_times[date] = []

        # Инициализация расписания, если оно не существует
        if date not in self.booking_handler.schedule:
            self.booking_handler.schedule[date] = {
                datetime.time(hour, minute): False
                for hour in range(9, 18)
                for minute in [0, 30]
            }

        markup = types.InlineKeyboardMarkup()
        for time, available in self.booking_handler.schedule[date].items():
            formatted_time = time.strftime("%H:%M")
            callback_data = f'unlock_time_{date}_{formatted_time}'
            if time in self.selected_times[date]:
                time_button = types.InlineKeyboardButton(text=f"✅ {formatted_time}", callback_data=callback_data)
                print(f"Slot {formatted_time} is selected")
            elif not available:
                time_button = types.InlineKeyboardButton(text=formatted_time, callback_data=callback_data)
                print(f"Slot {formatted_time} is not selected")
            else:
                continue
            markup.add(time_button)
        done_button = types.InlineKeyboardButton(text="Готово", callback_data=f'done_unlock_{date}')
        back_button = types.InlineKeyboardButton(text="Назад", callback_data=f'back_to_unlock_dates_{date}')
        markup.add(done_button)
        markup.add(back_button)
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   text=f"Выберите слоты для разблокировки на {date.strftime('%d.%m %A')}:",
                                   reply_markup=markup)

    def unlock_time(self, call, date, time):
        """Добавляет или убирает выбранный временной слот из списка."""
        print(f"unlock_time called with date: {date}, time: {time}")
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        time = datetime.datetime.strptime(time, "%H:%M").time()
        print(f"Current selected times: {self.selected_times}")
        if date not in self.selected_times:
            self.selected_times[date] = []
        if time in self.selected_times[date]:
            self.selected_times[date].remove(time)
            print(f"Slot {time} removed from selected_times")
        else:
            self.selected_times[date].append(time)
            print(f"Slot {time} added to selected_times")
        self.show_unlock_times(call, str(date))  # Обновляем кнопки, чтобы показать текущий выбор

    def confirm_unlock(self, call, date):
        """Подтверждает разблокировку выбранных временных слотов и возвращает к выбору дат."""
        print(f"confirm_unlock called with date: {date}")
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        for time in self.selected_times[date]:
            self.booking_handler.admin_unlock_slot(str(date), str(time))
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   text=f"Слоты на {date.strftime('%d.%m %A')} разблокированы")
        del self.selected_times[date]  # Очистка выбранных слотов после разблокировки
        self.show_unlock_dates(call)  # Возвращаемся к выбору дат

    def send_bookings(self, call):
        """Отправляет владельцу список текущих записей на неделю."""
        print("send_bookings called")
        bookings = self.booking_handler.get_bookings()
        notify_owner(self.bot, bookings)
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Список записей отправлен владельцу.")
