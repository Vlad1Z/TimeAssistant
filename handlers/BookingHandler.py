import datetime
from telebot import types
import locale

# Устанавливаем русскую локаль
locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

class BookingHandler:
    """
    Класс BookingHandler управляет процессом записи пользователя на прием.
    """
    def __init__(self, bot):
        """Инициализирует обработчик с экземпляром бота.
        :param bot: Экземпляр телеграм-бота.
        """
        self.bot = bot
        self.schedule = self.generate_initial_schedule()
        self.current_booking_type = {}

    def generate_initial_schedule(self):
        """Генерирует начальный график, где все слоты заблокированы."""
        schedule = {}
        start_date = datetime.date.today()
        for day in range(7):  # генерируем расписание на неделю
            date = start_date + datetime.timedelta(days=day)
            schedule[date] = {}
            current_time = datetime.datetime.combine(date, datetime.time(9, 0))
            end_time = datetime.datetime.combine(date, datetime.time(18, 0))
            while current_time < end_time:
                schedule[date][current_time.time()] = False  # Все слоты заблокированы
                current_time += datetime.timedelta(minutes=30)
        return schedule

    def handle(self, message):
        """
        Обрабатывает запрос на запись, показывая типы записи.
        :param message: Сообщение от пользователя.
        """
        print("handle called")
        self.show_booking_types(message)

    def show_booking_types(self, message):
        """Отображает пользователю типы записи."""
        print("show_booking_types called")
        markup = types.InlineKeyboardMarkup()
        type1_button = types.InlineKeyboardButton(text="Тип 1 (Консультация)", callback_data='type_1')
        type2_button = types.InlineKeyboardButton(text="Тип 2 (Процедура)", callback_data='type_2')
        back_button = types.InlineKeyboardButton(text="Назад", callback_data='back_to_main')
        markup.add(type1_button)
        markup.add(type2_button)
        markup.add(back_button)
        self.bot.send_message(message.chat.id, "Выберите тип записи:", reply_markup=markup)

    def show_available_slots(self, call, booking_type):
        """Отображает пользователю доступные даты."""
        print(f"show_available_slots called with booking_type: {booking_type}")
        self.current_booking_type[call.from_user.id] = booking_type
        markup = types.InlineKeyboardMarkup()
        for date, times in self.schedule.items():
            formatted_date = date.strftime("%d.%m %A").capitalize()
            date_button = types.InlineKeyboardButton(text=formatted_date, callback_data=f'date_{date}')
            markup.add(date_button)
        back_button = types.InlineKeyboardButton(text="Назад", callback_data='back_to_types')
        markup.add(back_button)
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите дату:", reply_markup=markup)

    def show_times(self, call, date):
        """Отображает доступные временные слоты для выбранной даты."""
        print(f"show_times called with date: {date}")
        booking_type = self.current_booking_type.get(call.from_user.id)
        interval = 30 if booking_type == 'type_1' else 60
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        markup = types.InlineKeyboardMarkup()
        print(f"show_times: {self.schedule[date]}")  # Логирование доступных слотов
        for time, available in self.schedule[date].items():
            if available:
                if time.minute % interval == 0:
                    formatted_time = time.strftime("%H:%M")
                    time_button = types.InlineKeyboardButton(text=formatted_time, callback_data=f'time_{date}_{time}')
                    markup.add(time_button)
                    print(f"Adding available slot: {formatted_time}")  # Логирование добавленных слотов
        back_button = types.InlineKeyboardButton(text="Назад", callback_data=f'back_to_dates_{booking_type}')
        markup.add(back_button)
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Доступные слоты на {date.strftime('%d.%m %A').capitalize()}:", reply_markup=markup)

    def book_time(self, call, date, time):
        """Записывает пользователя на выбранный временной слот."""
        print(f"book_time called with date: {date}, time: {time}")
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        time = datetime.datetime.strptime(time, "%H:%M").time()
        self.schedule[date][time] = False  # Блокируем слот
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы записаны на {date.strftime('%d.%m %A').capitalize()} в {time.strftime('%H:%M')}")
        # Отправляем уведомление владельцу
        from utils import notify_owner
        notify_owner(self.bot, f"Пользователь {call.message.chat.username} записан на {date.strftime('%d.%m %A').capitalize()} в {time.strftime('%H:%M')}")

    def admin_unlock_slot(self, date, time):
        print(f"admin_unlock_slot called with date: {date}, time: {time}")
        try:
            time = datetime.datetime.strptime(time, "%H:%M:%S").time()
        except ValueError:
            time = datetime.datetime.strptime(time, "%H:%M").time()
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        if date not in self.schedule:
            self.schedule[date] = {}
        self.schedule[date][time] = True  # Обозначаем слот как разблокированный
        print(f"Slot {time} on {date} unlocked")

    def show_admin_slots(self, call):
        """Отображает администратору слоты для разблокировки."""
        print("show_admin_slots called")
        markup = types.InlineKeyboardMarkup()
        for date, times in self.schedule.items():
            formatted_date = date.strftime("%d.%m %A").capitalize()
            date_button = types.InlineKeyboardButton(text=formatted_date, callback_data=f'admin_date_{date}')
            markup.add(date_button)
        back_button = types.InlineKeyboardButton(text="Назад", callback_data='back_to_main')
        markup.add(back_button)
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Выберите дату для разблокировки слотов:", reply_markup=markup)

    def show_admin_times(self, call, date):
        """Отображает администратору временные слоты для разблокировки."""
        print(f"show_admin_times called with date: {date}")
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        markup = types.InlineKeyboardMarkup()
        for time, available in self.schedule[date].items():
            if not available:
                time_button = types.InlineKeyboardButton(text=str(time), callback_data=f'admin_time_{date}_{time}')
                markup.add(time_button)
        back_button = types.InlineKeyboardButton(text="Назад", callback_data='back_to_admin_dates')
        markup.add(back_button)
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Заблокированные слоты на {date.strftime('%d.%m %A').capitalize()}:", reply_markup=markup)

    def admin_unlock_time(self, call, date, time):
        """Разблокирует выбранный временной слот."""
        print(f"admin_unlock_time called with date: {date}, time: {time}")
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        time = datetime.datetime.strptime(time, "%H:%M:%S").time()
        self.schedule[date][time] = True
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Слот на {date.strftime('%d.%m %A').capitalize()} в {time.strftime('%H:%M')} разблокирован")

    def get_bookings(self):
        """Возвращает список текущих записей на неделю."""
        print("get_bookings called")
        bookings = "Текущие записи на неделю:\n"
        start_date = datetime.date.today()
        for week in range(3):  # Проверяем расписание на три недели
            for day in range(7):
                date = start_date + datetime.timedelta(days=day + week * 7)
                bookings += f"\n{date.strftime('%d.%m %A').capitalize()}:\n"
                for time, available in self.schedule[date].items():
                    if not available:
                        bookings += f"  {time.strftime('%H:%M')}\n"
        return bookings
