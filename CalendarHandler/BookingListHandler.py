from utils import notify_owner

class BookingListHandler:
    def __init__(self, bot, booking_handler):
        self.bot = bot
        self.booking_handler = booking_handler

    def send_bookings(self, call):
        print("send_bookings called")
        bookings = self.booking_handler.get_bookings()
        notify_owner(self.bot, bookings)
        self.bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                   text="Список записей отправлен владельцу.")
