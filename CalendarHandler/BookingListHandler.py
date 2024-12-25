from utils import notify_owner

class BookingListHandler:
    def __init__(self, bot, booking_handler):
        """
        Инициализация обработчика списка записей.
        :param bot: Экземпляр бота.
        :param booking_handler: Экземпляр обработчика бронирования.
        """
        self.bot = bot
        self.booking_handler = booking_handler

    def send_bookings(self, call):
        """
        Отправляет список текущих бронирований владельцу.
        1. Получает список всех записей с помощью метода `get_bookings` из `booking_handler`.
        2. Отправляет этот список владельцу с помощью функции `notify_owner`.
        3. Отправляет сообщение пользователю, информируя его, что список записей был отправлен владельцу.
        :param call: Объект вызова, содержащий данные о сообщении пользователя.
        """
        print("send_bookings called")
        bookings = self.booking_handler.get_bookings()  # Получаем список бронирований
        notify_owner(self.bot, bookings)  # Отправляем список владельцу
        # Информируем пользователя, что список записей был отправлен владельцу
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   text="Список записей отправлен владельцу.")
