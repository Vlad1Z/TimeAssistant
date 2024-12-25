import datetime
from telebot import types

class UnlockTimeHandler:
    def __init__(self, bot, booking_handler):
        self.bot = bot
        self.booking_handler = booking_handler
        self.selected_times = {}

    def show_unlock_dates(self, call):
        """
                Отображает доступные даты для разблокировки слотов.
                Генерирует календарь на три недели вперед, где каждая дата является кнопкой,
                по которой можно выбрать дату для дальнейшей разблокировки времени.
                :param call: Объект вызова с данными о сообщении пользователя.
                """
        print("show_unlock_dates called")
        markup = types.InlineKeyboardMarkup()
        start_date = datetime.date.today()
        for week in range(3):
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
        """
                Отображает доступные временные слоты для выбранной даты.
                Для каждого слота, доступного для разблокировки, создается кнопка,
                на которой можно выбрать конкретное время. Отображаются только те слоты,
                которые еще не заблокированы.
                :param call: Объект вызова с данными о сообщении пользователя.
                :param date: Дата для отображения слотов.
                """
        print(f"show_unlock_times called with date: {date}")
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        if date not in self.selected_times:
            self.selected_times[date] = []

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
        """
                Обрабатывает добавление или удаление выбранных временных слотов для разблокировки.
                Если слот уже выбран, он будет удален, если нет — добавлен.
                После обновления списка выбранных слотов, метод вызывает повторное отображение слотов для выбранной даты.
                :param call: Объект вызова с данными о сообщении пользователя.
                :param date: Дата для разблокировки слота.
                :param time: Время для разблокировки слота.
                """
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
        self.show_unlock_times(call, str(date))

    def confirm_unlock(self, call, date):
        """
                Подтверждает разблокировку выбранных временных слотов для указанной даты.
                После успешного подтверждения все выбранные слоты разблокируются и отправляется уведомление.
                Метод очищает список выбранных слотов для данной даты и возвращает пользователя к выбору дат.
                :param call: Объект вызова с данными о сообщении пользователя.
                :param date: Дата, для которой нужно подтвердить разблокировку слотов.
                """
        print(f"confirm_unlock called with date: {date}")
        date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        for time in self.selected_times[date]:
            self.booking_handler.admin_unlock_slot(str(date), str(time))
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   text=f"Слоты на {date.strftime('%d.%m %A')} разблокированы")
        del self.selected_times[date]
        self.show_unlock_dates(call)
