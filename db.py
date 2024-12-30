import sqlite3
import pytz
from datetime import datetime, timedelta


# ===== Настройки базы данных =====
DB_NAME = "appointments.db"
TIMEZONE = "Europe/Moscow"

# ===== Вспомогательные функции =====
def get_local_time():
    """Возвращает текущее время с учётом часового пояса."""
    tz = pytz.timezone(TIMEZONE)
    local_time = datetime.now(tz)
    return local_time.strftime('%Y-%m-%d %H:%M:%S')

# ===== Управление таблицами =====
def create_tables():
    """Создаёт все необходимые таблицы."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблица записей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_user_id INTEGER NOT NULL,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        phone_number TEXT,
        appointment_date DATE,
        appointment_time TIME,
        request_date DATETIME,
        comments TEXT,
        status TEXT,
        message_id INTEGER
    );
    """)

    # Таблица посещений пользователей
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_visits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_user_id INTEGER NOT NULL,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        visit_date DATETIME,
        unique_until DATETIME,
        last_action TEXT
    );
    """)

    # Добавление уникального индекса для telegram_user_id
    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_telegram_user_id ON user_visits(telegram_user_id);
    """)

    conn.commit()
    conn.close()

# ===== Операции с таблицей records =====
def save_appointment(user_id, username, first_name, last_name, phone_number, date, time, comments, status):
    """Сохраняет запись в базе данных. Обновляет запись, если она уже существует."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Проверяем, существует ли запись с таким telegram_user_id и appointment_date
    cursor.execute("""
        SELECT id FROM records
        WHERE telegram_user_id = ? AND appointment_date = ?;
    """, (user_id, date))
    existing_record = cursor.fetchone()

    if existing_record:
        # Если запись существует, обновляем её
        cursor.execute("""
            UPDATE records
            SET username = ?, first_name = ?, last_name = ?, phone_number = ?, 
                appointment_time = ?, comments = ?, status = ?
            WHERE id = ?;
        """, (username, first_name, last_name, phone_number, time, comments, status, existing_record[0]))
    else:
        # Если записи нет, создаём новую
        cursor.execute("""
            INSERT INTO records (
                telegram_user_id, username, first_name, last_name, phone_number, 
                appointment_date, appointment_time, comments, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (user_id, username, first_name, last_name, phone_number, date, time, comments, status))

    conn.commit()
    conn.close()

def save_message_id_to_db(record_id, message_id):
    """Сохраняет message_id для конкретной записи."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE records
        SET message_id = ?
        WHERE id = ?;
    """, (message_id, record_id))

    conn.commit()
    conn.close()


def update_appointment(user_id, appointment_date, appointment_time, status, comment=None):
    """Обновляет запись в базе данных."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Проверяем и форматируем время в ЧЧ:ММ
    try:
        appointment_time = datetime.strptime(appointment_time, '%H:%M').strftime('%H:%M')
    except ValueError:
        raise ValueError("Некорректный формат времени. Время должно быть в формате ЧЧ:ММ.")

    cursor.execute("""
        UPDATE records
        SET appointment_date = ?, appointment_time = ?, status = ?, comments = ?
        WHERE id = ?;
    """, (appointment_date, appointment_time, status, comment, user_id))

    conn.commit()
    conn.close()

def get_last_appointment_id(user_id):
    """Возвращает последний ID записи для пользователя."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM records
        WHERE telegram_user_id = ? AND status = 'ожидает'
        ORDER BY id DESC LIMIT 1;
    """, (user_id,))
    result = cursor.fetchone()

    conn.close()
    return result[0] if result else None

def check_appointment_exists(record_id):
    """Проверяет существование записи в базе данных."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM records WHERE id = ?;", (record_id,))
    exists = cursor.fetchone() is not None

    conn.close()
    return exists

# ===== Операции с таблицей user_visits =====
def save_user_visit(user_id, username, first_name, last_name):
    """Логирует посещение пользователя в боте."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    visit_date = datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')
    unique_until = (datetime.now(pytz.timezone(TIMEZONE)) + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')

    # Проверяем, существует ли пользователь в таблице
    cursor.execute("""
        SELECT id FROM user_visits WHERE telegram_user_id = ?;
    """, (user_id,))
    result = cursor.fetchone()

    if result:
        # Если пользователь уже есть, обновляем запись
        cursor.execute("""
            UPDATE user_visits
            SET visit_date = ?, unique_until = ?, username = ?, first_name = ?, last_name = ?
            WHERE telegram_user_id = ?;
        """, (visit_date, unique_until, username, first_name, last_name, user_id))
    else:
        # Если пользователя нет, добавляем новую запись
        cursor.execute("""
            INSERT INTO user_visits (
                telegram_user_id, username, first_name, last_name, visit_date, unique_until
            )
            VALUES (?, ?, ?, ?, ?, ?);
        """, (user_id, username, first_name, last_name, visit_date, unique_until))

    conn.commit()
    conn.close()

def get_user_data_by_record_id(record_id):
    """Возвращает данные пользователя по ID записи."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT telegram_user_id, username, first_name, last_name, phone_number, message_id
        FROM records
        WHERE id = ?;
    """, (record_id,))
    result = cursor.fetchone()

    conn.close()
    if result:
        return {
            "telegram_user_id": result[0],
            "username": result[1],
            "first_name": result[2],
            "last_name": result[3],
            "phone_number": result[4],
            "message_id": result[5]  # Добавляем message_id в результат
        }
    return None

def get_unique_users():
    """Возвращает список уникальных пользователей на основании unique_until."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Получаем текущую дату и время
    current_time = datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')

    # Фильтруем пользователей, у которых unique_until >= текущей даты
    cursor.execute("""
        SELECT telegram_user_id, username, first_name, last_name, visit_date, unique_until
        FROM user_visits
        WHERE unique_until > ?;  -- Дата должна быть в будущем
    """, (current_time,))

    users = cursor.fetchall()
    conn.close()

    # Преобразуем данные в удобный формат
    return [
        {
            "telegram_user_id": user[0],
            "username": user[1],
            "first_name": user[2],
            "last_name": user[3],
            "visit_date": user[4],
            "unique_until": user[5],
        }
        for user in users
    ]

def get_repeat_visits():
    """Возвращает количество пользователей с повторными посещениями."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT telegram_user_id, COUNT(*) as visit_count
            FROM user_visits
            GROUP BY telegram_user_id
            HAVING visit_count > 1
        );
    """)
    result = cursor.fetchone()[0]
    conn.close()
    return result

def get_inactive_users():
    """Возвращает список неактивных пользователей (не заходивших более 30 дней)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Получаем текущую дату и время
    current_time = datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')

    # Фильтруем пользователей, которые неактивны более 30 дней
    cursor.execute("""
        SELECT telegram_user_id, username, first_name, last_name, visit_date, unique_until
        FROM user_visits
        WHERE visit_date <= datetime(?, '-30 days');
    """, (current_time,))

    users = cursor.fetchall()
    conn.close()

    # Преобразуем данные в удобный формат
    return [
        {
            "telegram_user_id": user[0],
            "username": user[1],
            "first_name": user[2],
            "last_name": user[3],
            "visit_date": user[4],
            "unique_until": user[5],
        }
        for user in users
    ]


def log_user_action(user_id, username, action_type, action_details=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Текущее время для логирования
    action_time = datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')
    unique_until = (datetime.now(pytz.timezone(TIMEZONE)) + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')

    # Обновляем или создаем запись
    cursor.execute("""
        INSERT INTO user_visits (telegram_user_id, username, visit_date, unique_until, last_action)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(telegram_user_id) DO UPDATE SET
            visit_date = excluded.visit_date,
            unique_until = excluded.unique_until,
            last_action = excluded.last_action;
    """, (user_id, username, action_time, unique_until, action_type))

    conn.commit()
    conn.close()


# Вспомогательная функция для получения записей из базы данных
# Реализуем ее в файле db.py
def get_records_from_today():
    """Получает записи с текущей даты и времени."""

    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()

    # Получаем текущую дату и время
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Выполняем запрос к базе данных
    cursor.execute("""
        SELECT id, telegram_user_id, username, first_name, last_name, phone_number,
               appointment_date, appointment_time, comments, status
        FROM records
        WHERE datetime(appointment_date || ' ' || appointment_time) >= datetime(?)
        ORDER BY appointment_date, appointment_time ASC;
    """, (current_datetime,))

    rows = cursor.fetchall()
    conn.close()

    # Преобразуем результаты в удобный формат
    return [
        {
            "id": row[0],
            "telegram_user_id": row[1],
            "username": row[2],
            "first_name": row[3],
            "last_name": row[4],
            "phone_number": row[5],
            "appointment_date": row[6],
            "appointment_time": row[7],
            "comments": row[8],
            "status": row[9]
        }
        for row in rows
    ]

# ===== Инициализация базы данных =====
if __name__ == "__main__":
    create_tables()
