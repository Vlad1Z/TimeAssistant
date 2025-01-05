from db import log_user_action
from config import id_chat_owner


# Декоратор для логирования
def log_action(action_type, action_details=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            obj = args[0] if args else None
            if obj:
                if hasattr(obj, 'message') and hasattr(obj, 'from_user'):
                    # Для CallbackQuery
                    user_id = obj.message.chat.id
                    username = obj.from_user.username
                    first_name = obj.from_user.first_name
                    last_name = obj.from_user.last_name
                elif hasattr(obj, 'chat') and hasattr(obj, 'from_user'):
                    # Для Message
                    user_id = obj.chat.id
                    username = obj.from_user.username
                    first_name = obj.from_user.first_name
                    last_name = obj.from_user.last_name
                else:
                    # Неподдерживаемый тип
                    return func(*args, **kwargs)

                # Исключение для администратора
                if str(user_id) == id_chat_owner:
                    return func(*args, **kwargs)

                log_user_action(user_id, username, first_name, last_name, action_type, action_details)
            return func(*args, **kwargs)
        return wrapper
    return decorator


