def notify_owner(bot, message):
    """Отправляет уведомление владельцу бота."""
    from config import id_chat_owner
    bot.send_message(id_chat_owner, message)
