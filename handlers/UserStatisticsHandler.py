from telebot import types
from datetime import datetime, timedelta
from db import get_users_by_date_range, get_repeat_visits, get_inactive_users

class BaseStatisticsHandler:
    """
    Базовый класс для работы с разделами статистики.
    Содержит общие методы и логику для всех типов статистики.
    """
    def __init__(self, bot):
        self.bot = bot
        self.pending_section = {}  # Для хранения выбранного раздела статистики

    def show_statistics(self, message):
        """
        Отображает главное меню статистики пользователей.
        - Выводит основные разделы статистики: уникальные пользователи, повторные посещения, неактивные пользователи, посещённые разделы.
        - Отправляет сообщение с кнопками для выбора раздела.
        """
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

    def handle_back_to_menu(self, call):
        from handlers.StartHandler import StartHandler
        start_handler = StartHandler(self.bot)
        start_handler.main_menu(call.message)


class UniqueUsersStatisticsHandler(BaseStatisticsHandler):
    def handle_statistics(self, call):
        self.request_date_range_unique_user(call)  # Для уникальных пользователей требуется ввод дат

    def request_date_range_unique_user(self, call):
        """
        Запрашивает диапазон дат у администратора.
        - Отправляет сообщение с подсказками для ввода диапазона дат.
        - Показывает примеры для выбора периода: за день, неделю, две недели, месяц или всё время.
        """
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

    def process_date_input_unique_users(self, message):
        """Обрабатывает ввод дат пользователем для уникальных пользователей."""
        try:
            dates = message.text.split()
            if len(dates) != 2:
                raise ValueError("Неверный формат")

            start_date = datetime.strptime(dates[0], '%d.%m.%Y').date()
            end_date = datetime.strptime(dates[1], '%d.%m.%Y').date()

            if start_date > end_date:
                raise ValueError("Начальная дата больше конечной")

            # Генерация статистики
            self.generate_statistics_unique_users(message.chat.id, start_date, end_date)

        except ValueError as e:
            self.bot.send_message(
                message.chat.id,
                f"❌ Ошибка: {str(e)}\nПопробуйте снова. Пример: <code>01.01.2025 15.01.2025</code>",
                parse_mode="HTML"
            )

    def generate_statistics_unique_users(self, chat_id, start_date, end_date):
        """
        Генерирует статистику уникальных пользователей за указанный период.
        - Извлекает данные из базы через get_users_by_date_range.
        - Форматирует данные для удобного чтения.
        - Отправляет сообщение пользователю с результатами или уведомляет об отсутствии данных.
        """
        stats = get_users_by_date_range(start_date, end_date, unique=True)

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
                f"📊 Уникальные пользователи за период {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}:\n\n"
                f"{readable_stats}",
                parse_mode="HTML"
            )
        else:
            self.bot.send_message(
                chat_id,
                f"❌ Данных о уникальных пользователях за период {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')} нет.",
                parse_mode="HTML"
            )


class RepeatVisitsStatisticsHandler(BaseStatisticsHandler):
    """
    Класс для работы с повторными посещениями.
    Содержит методы для генерации и обработки статистики повторных посещений.
    """

    def handle_statistics(self, call):
        self.generate_statistics_repeat_visits(call.message.chat.id)  # Не требует ввода дат

    def generate_statistics_repeat_visits(self, chat_id):
        """
        Генерирует статистику повторных посещений.
        - Выводит пользователей с повторной активностью (например, заходили в бота несколько раз).
        """
        stats = get_repeat_visits()  # Предполагается, что возвращает список записей

        if isinstance(stats, int):  # Если вернулось число вместо списка
            self.bot.send_message(
                chat_id,
                f"📊 Повторных посещений: {stats}",
                parse_mode="HTML"
            )
            return

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
                f"📊 Статистика повторных посещений:\n\n{readable_stats}",
                parse_mode="HTML"
            )
        else:
            self.bot.send_message(
                chat_id,
                "❌ Нет данных о повторных посещениях.",
                parse_mode="HTML"
            )

class InactiveUsersStatisticsHandler(BaseStatisticsHandler):
    """
    Класс для работы с неактивными пользователями.
    Содержит методы для генерации и обработки статистики неактивных пользователей.
    """
    def handle_statistics(self, call):
        self.request_date_range_inactive_users(call)  # Для неактивных пользователей требуется ввод дат

    def request_date_range_inactive_users(self, call):
        """
        Запрашивает диапазон дат для неактивных пользователей.
        - Показывает подсказки с примерами для выбора периода.
        """
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)
        month_ago = today - timedelta(days=30)
        two_months_ago = today - timedelta(days=60)

        message_text = (
            "📅 Введите диапазон дат в формате: <code>ДД.ММ.ГГ ДД.ММ.ГГ</code>\n\n"
            "Пример:\n"
            f"👉 За неделю: <code>{week_ago.strftime('%d.%m.%Y')} {today.strftime('%d.%m.%Y')}</code>\n"
            f"👉 За две недели: <code>{two_weeks_ago.strftime('%d.%m.%Y')} {today.strftime('%d.%m.%Y')}</code>\n"
            f"👉 За месяц: <code>{month_ago.strftime('%d.%m.%Y')} {today.strftime('%d.%m.%Y')}</code>\n"
            f"👉 За два месяца: <code>{two_months_ago.strftime('%d.%m.%Y')} {today.strftime('%d.%m.%Y')}</code>\n"
        )

        self.bot.send_message(
            call.message.chat.id,
            message_text,
            parse_mode="HTML"
        )

    def process_date_input_inactive_users(self, message):
        """
        Обрабатывает ввод дат для поиска неактивных пользователей.
        """
        try:
            dates = message.text.split()
            if len(dates) != 2:
                raise ValueError("Неверный формат")

            start_date = datetime.strptime(dates[0], '%d.%m.%Y').date()
            end_date = datetime.strptime(dates[1], '%d.%m.%Y').date()

            if start_date > end_date:
                raise ValueError("Начальная дата больше конечной")

            self.generate_statistics_inactive_users(message.chat.id, start_date, end_date)

        except ValueError as e:
            self.bot.send_message(
                message.chat.id,
                f"❌ Ошибка: {str(e)}\nПопробуйте снова. Пример: <code>29.12.2024 05.01.2025</code>",
                parse_mode="HTML"
            )

    def generate_statistics_inactive_users(self, chat_id, start_date, end_date):
        """
        Генерирует статистику неактивных пользователей за указанный период.
        """
        stats = get_inactive_users(start_date, end_date)

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
                f"📊 Неактивные пользователи за период {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}:\n\n"
                f"{readable_stats}",
                parse_mode="HTML"
            )
        else:
            self.bot.send_message(
                chat_id,
                f"❌ Нет данных о неактивных пользователях за период {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}.",
                parse_mode="HTML"
            )


class VisitedSectionsStatisticsHandler(BaseStatisticsHandler):
    """
    Класс для анализа посещённых разделов бота.
    Содержит методы для сбора и обработки данных по посещённым разделам.
    """


