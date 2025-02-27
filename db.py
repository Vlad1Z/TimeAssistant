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
        action_type TEXT,
        action_details TEXT
    );
    """)

    conn.commit()
    conn.close()

# ===== Операции с таблицей records =====
def save_appointment(user_id, username, first_name, last_name, phone_number, date, time, request_date, comments, status):
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
                appointment_time = ?, comments = ?, status = ?, request_date = ?
            WHERE id = ?;
        """, (username, first_name, last_name, phone_number, time, comments, status, request_date, existing_record[0]))
    else:
        # Если записи нет, создаём новую
        cursor.execute("""
            INSERT INTO records (
                telegram_user_id, username, first_name, last_name, phone_number, 
                appointment_date, appointment_time, request_date, comments, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (user_id, username, first_name, last_name, phone_number, date, time, request_date, comments, status))

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

    cursor.execute("""
        UPDATE records
        SET appointment_date = ?, appointment_time = ?, status = ?, comments = ?
        WHERE id = ?;
    """, (appointment_date, appointment_time, status, comment, user_id))  # user_id здесь должен быть record_id

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
    """
    Возвращает список пользователей с повторной активностью, включая данные о том, оставляли ли они номер телефона.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        SELECT 
            uv.telegram_user_id, 
            uv.username, 
            uv.first_name, 
            uv.last_name, 
            MAX(uv.visit_date) as last_visit, 
            MAX(CASE WHEN uv.action_details = 'Отправить номер телефона' THEN uv.visit_date END) as phone_action_date, 
            COUNT(*) as visit_count
        FROM user_visits uv
        GROUP BY uv.telegram_user_id
        HAVING COUNT(*) > 1
    """
    cursor.execute(query)
    result = cursor.fetchall()
    conn.close()

    return [
        {
            "telegram_user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "visit_date": row[4],
            "phone_action_date": row[5],  # Дата, когда пользователь отправлял номер телефона (или None)
            "visit_count": row[6]
        }
        for row in result
    ]




def get_inactive_users(start_date, end_date):
    """
    Возвращает список неактивных пользователей за указанный период.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = """
        SELECT telegram_user_id, username, first_name, last_name, MAX(visit_date) as last_visit
        FROM user_visits
        WHERE DATE(visit_date) NOT BETWEEN ? AND ?
        GROUP BY telegram_user_id
    """

    cursor.execute(query, (start_date, end_date))
    result = cursor.fetchall()
    conn.close()

    # Преобразуем результат в читаемый формат
    return [
        {
            "telegram_user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "visit_date": row[4]
        }
        for row in result
    ]



def log_user_action(user_id, username, first_name, last_name, action_type, action_details=None):
    """Логирует действия пользователя в базу данных."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Текущее время для логирования
    action_time = datetime.now(pytz.timezone(TIMEZONE)).strftime('%Y-%m-%d %H:%M:%S')

    # Добавляем запись в таблицу
    cursor.execute("""
        INSERT INTO user_visits (telegram_user_id, username, first_name, last_name, visit_date, action_type, action_details)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (user_id, username, first_name, last_name, action_time, action_type, action_details))

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






def get_users_by_date_range(start_date, end_date, unique=False, repeat=False, inactive=False):
    """Получает пользователей по диапазону дат с опциональной фильтрацией."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    base_query = """
        SELECT telegram_user_id, username, first_name, last_name, visit_date
        FROM user_visits
        WHERE DATE(visit_date) BETWEEN ? AND ?
    """

    if unique:
        # Уникальные пользователи
        query = f"{base_query} GROUP BY telegram_user_id"
    elif repeat:
        # Повторные посещения
        query = f"""
            SELECT telegram_user_id, username, first_name, last_name, MAX(visit_date) as last_visit, COUNT(*)
            FROM user_visits
            WHERE DATE(visit_date) BETWEEN ? AND ?
            GROUP BY telegram_user_id
            HAVING COUNT(*) > 1
        """
    elif inactive:
        # Неактивные пользователи (не заходили более 30 дней)
        query = f"{base_query} AND DATE(visit_date) < DATE('now', '-30 days')"
    else:
        # Все пользователи
        query = base_query

    cursor.execute(query, (start_date, end_date))
    result = cursor.fetchall()
    conn.close()

    # Преобразуем результат в читаемый формат
    return [
        {
            "telegram_user_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "visit_date": row[4]
        }
        for row in result
    ]



# ===== Инициализация базы данных =====
if __name__ == "__main__":
    create_tables()
