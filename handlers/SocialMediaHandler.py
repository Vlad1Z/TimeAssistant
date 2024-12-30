from telebot import types


class SocialMediaHandler:
    def __init__(self, bot):
        self.bot = bot

    def show_social_media(self, message):
        """Отправляет информацию о социальных сетях."""
        # Текст сообщения
        social_media_message = (
            "💖 Давайте оставаться на связи! Я выкладываю полезные посты, делюсь акциями, розыгрышами и новостями в Instagram.\n\n"
            "📸 <b>Мой Instagram:</b> <a href='https://www.instagram.com/your_instagram'>@your_instagram</a>\n\n"
            "Подписывайтесь, чтобы быть в курсе всех обновлений! 🥰"
        )

        # Отправка сообщения с кнопкой-ссылкой
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(
                "📲 Перейти в Instagram", url="https://www.instagram.com/your_instagram"
            )
        )

        self.bot.send_message(
            message.chat.id,
            social_media_message,
            reply_markup=markup,
            parse_mode="HTML",
            disable_web_page_preview=False  # Можно отключить или включить превью ссылки
        )
