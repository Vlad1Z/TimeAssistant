import sqlite3
from datetime import datetime, timedelta
import pytz

def create_table():
    """Создаёт таблицу с актуальной схемой."""
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()

    # Удаляем таблицу, если она существует
    cursor.execute("DROP TABLE IF EXISTS records;")

    # Создаём таблицу с правильными колонками
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_user_id INTEGER NOT NULL,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        phone_number TEXT,
        appointment_date TEXT,
        appointment_time TEXT,
        request_date TEXT,
        comments TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

def get_local_time():
    """Возвращает текущее время с учётом часового пояса."""
    tz = pytz.timezone('Europe/Moscow')  # Ваш часовой пояс (например, Москва)
    local_time = datetime.now(tz)
    return local_time.strftime('%Y-%m-%d %H:%M:%S')

def save_appointment(user_id, username, first_name, last_name, phone_number, date, time, comments, status="ожидает"):
    # Подключаемся к базе данных
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()

    # Получаем время запроса с учётом часового пояса
    request_date = get_local_time()

    # Добавляем запись в таблицу
    cursor.execute("""
    INSERT INTO records (telegram_user_id, username, first_name, last_name, phone_number, appointment_date, appointment_time, request_date, comments, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, first_name, last_name, phone_number, date, time, request_date, comments, status))

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

# Вызовем функцию для создания таблицы
create_table()

def update_appointment(user_id, appointment_date, appointment_time, status, comment=None):
    """Обновляет запись в базе данных."""
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()

    # Обновляем запись по user_id
    cursor.execute("""
    UPDATE records
    SET appointment_date = ?, appointment_time = ?, status = ?, comments = ?
    WHERE telegram_user_id = ? AND status = 'ожидает'
    """, (appointment_date, appointment_time, status, comment, user_id))

    conn.commit()
    conn.close()



def create_table():
    """Создаёт таблицу для записи пользователей, которые заходят в бота."""
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()

    # Удаляем таблицу, если она существует
    cursor.execute("DROP TABLE IF EXISTS user_visits;")

    # Создаём таблицу для записи информации о пользователях
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_user_id INTEGER NOT NULL,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        visit_date TEXT,
        visit_time TEXT
    )
    """)

    conn.commit()
    conn.close()

def get_local_time():
    """Возвращает текущее время с учётом часового пояса."""
    tz = pytz.timezone('Europe/Moscow')  # Ваш часовой пояс (например, Москва)
    local_time = datetime.now(tz)
    return local_time.strftime('%Y-%m-%d %H:%M:%S')

def save_user_visit(user_id, username, first_name, last_name):
    """Логирует посещение пользователя в боте."""
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()

    # Получаем время посещения с учётом часового пояса
    visit_date = get_local_time()
    visit_time = datetime.now(pytz.timezone('Europe/Moscow')).strftime('%H:%M:%S')

    # Добавляем запись в таблицу посещений
    cursor.execute("""
    INSERT INTO user_visits (telegram_user_id, username, first_name, last_name, visit_date, visit_time)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, username, first_name, last_name, visit_date, visit_time))

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

# Вызовем функцию для создания таблицы
create_table()