class SocialMediaHandler:
    def __init__(self, bot):
        self.bot = bot

    def handle_social_media(self, message):
        """Отправляет информацию о социальных сетях."""
        self.bot.send_message(message.chat.id, "Наши социальные сети: ...")
