from telebot import types
from handlers.UserRequestHandler import UserRequestHandler  # Исправлен импорт

class ProceduresHandler:
    def __init__(self, bot, admin_chat_id):
        self.bot = bot
        self.admin_chat_id = admin_chat_id
        self.user_request_handler = UserRequestHandler(bot, admin_chat_id)  # Ссылка на существующий обработчик

    def show_procedures(self, message):
        """Отображает список процедур с кратким описанием."""
        procedures_message = (
            "💉 **Виды процедур и их описание:**\n\n"
            "1. **Ботокс инъекции** — разглаживают морщины, делают кожу молодой и сияющей. ✨\n"
            "2. **Гиалуроновая кислота** — увлажняет кожу, возвращает ей упругость. 💧\n"
            "3. **Мезотерапия лица** — улучшает текстуру кожи, устраняет мелкие недостатки. 🌸\n"
            "4. **Пилинг лица** — очищает кожу, устраняет пигментные пятна. 🌿\n\n"
            "Выберите интересующую процедуру, чтобы узнать больше. 😊"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("ℹ️ Узнать подробнее", callback_data="get_contact"))

        self.bot.send_message(message.chat.id, procedures_message, reply_markup=markup, parse_mode="Markdown")

    def handle_booking_procedure(self, call):
        """Обрабатывает нажатие кнопки 'Узнать подробнее'."""
        self.bot.answer_callback_query(call.id)  # Убираем индикатор загрузки
        self.user_request_handler.start_request(call.message)  # Перенаправляем к запросу контакта
