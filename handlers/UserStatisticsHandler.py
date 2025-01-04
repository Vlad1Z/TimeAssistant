from telebot import types
from datetime import datetime, timedelta
from db import get_users_by_date_range


class UserStatisticsHandler:
    def __init__(self, bot):
        self.bot = bot
        self.pending_section = {}  # Для хранения выбранного раздела статистики

    def show_statistics(self, message):
        """Отображает главное меню статистики пользователей."""
        statistics_message = (
            "📊 <b>Выберите раздел статистики:</b>\n\n"
            "После выбора раздела вы можете указать даты или выбрать стандартный период."
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("👥 Уникальные пользователи", callback_data="unique_users"))
        markup.add(types.InlineKeyboardButton("🔄 Повторные посещения", callback_data="repeat_visits"))
        markup.add(types.InlineKeyboardButton("📭 Неактивные пользователи", callback_data="inactive_users"))
        markup.add(types.InlineKeyboardButton("📊 Посещенные разделы", callback_data="section_stats"))
        markup.add(types.InlineKeyboardButton("🔙 Вернуться в главное меню", callback_data="back_to_menu"))

        self.bot.send_message(
            message.chat.id,
            statistics_message,
            reply_markup=markup,
            parse_mode="HTML"
        )

    def handle_detailed_statistics(self, call):
        """Обрабатывает выбор раздела статистики."""
        if call.data in ["unique_users", "repeat_visits", "inactive_users"]:
            self.pending_section[call.message.chat.id] = call.data  # Сохраняем выбранный раздел
            self.request_date_range(call)
        elif call.data == "section_stats":
            # Здесь можно добавить логику для анализа посещённых разделов
            self.bot.send_message(
                call.message.chat.id,
                "📊 Анализ посещённых разделов пока не реализован.",
                parse_mode="HTML"
            )
        elif call.data == "back_to_menu":
            # Возвращение в главное меню
            from handlers.StartHandler import StartHandler
            start_handler = StartHandler(self.bot)
            start_handler.main_menu(call.message)

    def request_date_range(self, call):
        """Запрашивает диапазон дат у администратора с примерами."""
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)
        month_ago = today - timedelta(days=30)
        all_time = "01.01.2000"

        message_text = (
            "📅 Введите диапазон дат в формате: <code>ДД.ММ.ГГ ДД.ММ.ГГ</code>\n\n"
            "Пример:\n"
            f"👉 За день: <code>{today.strftime('%d.%m.%Y')} {today.strftime('%d.%m.%Y')}</code>\n"
            f"👉 За неделю: <code>{week_ago.strftime('%d.%m.%Y')} {today.strftime('%d.%m.%Y')}</code>\n"
            f"👉 За две недели: <code>{two_weeks_ago.strftime('%d.%m.%Y')} {today.strftime('%d.%m.%Y')}</code>\n"
            f"👉 За месяц: <code>{month_ago.strftime('%d.%m.%Y')} {today.strftime('%d.%m.%Y')}</code>\n"
            f"👉 За всё время: <code>{all_time} {today.strftime('%d.%m.%Y')}</code>\n"
        )

        self.bot.send_message(
            call.message.chat.id,
            message_text,
            parse_mode="HTML"
        )

    def process_date_input(self, message):
        """Обрабатывает ввод дат пользователем."""
        try:
            dates = message.text.split()
            if len(dates) != 2:
                raise ValueError("Неверный формат")

            start_date = datetime.strptime(dates[0], '%d.%m.%Y').date()
            end_date = datetime.strptime(dates[1], '%d.%m.%Y').date()

            if start_date > end_date:
                raise ValueError("Начальная дата больше конечной")

            section = self.pending_section.pop(message.chat.id, None)
            if not section:
                raise ValueError("Не удалось определить раздел статистики")

            self.generate_statistics(message.chat.id, section, start_date, end_date)

        except ValueError as e:
            self.bot.send_message(
                message.chat.id,
                f"❌ Ошибка: {str(e)}\nПопробуйте снова. Пример: <code>01.01.2025 15.01.2025</code>",
                parse_mode="HTML"
            )

    def generate_statistics(self, chat_id, section, start_date, end_date):
        """Генерирует статистику за выбранный период."""
        if section == "unique_users":
            stats = get_users_by_date_range(start_date, end_date, unique=True)
        elif section == "repeat_visits":
            stats = get_users_by_date_range(start_date, end_date, repeat=True)
        elif section == "inactive_users":
            stats = get_users_by_date_range(start_date, end_date, inactive=True)
        else:
            stats = get_users_by_date_range(start_date, end_date)

        if stats:
            readable_stats = "\n\n".join([
                f"👤 Имя: {user['first_name']} {user['last_name'] or ''}\n"
                f"📧 Username: @{user['username'] if user['username'] else 'Не указан'}\n"
                f"🆔 ID: <code>{user['telegram_user_id']}</code>\n"
                f"🕒 Последний визит: {user['visit_date']}"
                for user in stats
            ])
            self.bot.send_message(
                chat_id,
                f"📊 Статистика ({section}) за период {start_date} - {end_date}:\n\n"
                f"{readable_stats}",
                parse_mode="HTML"
            )
        else:
            self.bot.send_message(
                chat_id,
                f"❌ Данных за период {start_date} - {end_date} нет.",
                parse_mode="HTML"
            )

