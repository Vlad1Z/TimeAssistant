from telebot import types
from db import get_records_from_today
from datetime import datetime


class RecordsHandler:
    def __init__(self, bot):
        self.bot = bot

    def show_records(self, message):
        """Показывает список записей начиная с сегодняшнего дня."""
        records = get_records_from_today()
        if not records:
            self.bot.send_message(
                message.chat.id,
                "❌ Нет записей на сегодня или позже.",
                parse_mode="HTML"
            )
            return

        # Формируем текст для отправки
        records_text = "📋 <b>Текущие записи:</b>\n\n"
        for record in records:
            # Форматируем дату в формате DD.MM.YY
            appointment_date = datetime.strptime(record['appointment_date'], '%Y-%m-%d').strftime('%d.%m.%y')

            records_text += (
                f"🆔 Заявка №{record['id']}\n"
                f"👤 Клиент: {record['first_name']} {record['last_name'] or ''}\n"
                f"📱 Телефон: {record['phone_number']}\n"
                f"📧 Username: @{record['username'] or 'Не указан'}\n"
                f"📅 Дата: {appointment_date}\n"
                f"⏰ Время: {record['appointment_time']}\n"
                f"💬 Комментарий: {record['comments'] or 'Нет'}\n"
                "-----------------------------\n"
            )

        # Отправляем пользователю
        self.bot.send_message(
            message.chat.id,
            records_text,
            parse_mode="HTML"
        )

