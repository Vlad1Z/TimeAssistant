import sqlite3
from datetime import datetime
import pytz

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
        appointment_date TEXT,
        appointment_time TEXT,
        request_date TEXT,
        comments TEXT,
        status TEXT,
        UNIQUE(telegram_user_id, appointment_date)
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
        visit_date TEXT,
        visit_time TEXT
    );
    """)

    conn.commit()
    conn.close()

# ===== Операции с таблицей records =====
def save_appointment(user_id, username, first_name, last_name, phone_number, date, time, comments, status):
    """Сохраняет или обновляет запись в базе данных."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO records (
            telegram_user_id, username, first_name, last_name, phone_number, appointment_date, appointment_time, comments, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(telegram_user_id, appointment_date) DO UPDATE SET
            appointment_time = excluded.appointment_time,
            comments = excluded.comments,
            status = excluded.status;
    """, (user_id, username, first_name, last_name, phone_number, date, time, comments, status))

    conn.commit()
    conn.close()

def update_appointment(user_id, appointment_date, appointment_time, status, comment=None):
    """Обновляет запись в базе данных."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

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

    visit_date = datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d')
    visit_time = datetime.now(pytz.timezone(TIMEZONE)).strftime('%H:%M:%S')

    cursor.execute("""
        INSERT INTO user_visits (
            telegram_user_id, username, first_name, last_name, visit_date, visit_time
        )
        VALUES (?, ?, ?, ?, ?, ?);
    """, (user_id, username, first_name, last_name, visit_date, visit_time))

    conn.commit()
    conn.close()

def get_user_data_by_record_id(record_id):
    """Возвращает данные пользователя по ID записи."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT telegram_user_id, username, first_name, last_name, phone_number
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
            "phone_number": result[4]
        }
    return None

# ===== Инициализация базы данных =====
if __name__ == "__main__":
    create_tables()
