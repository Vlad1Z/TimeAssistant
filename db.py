import sqlite3

def save_appointment(user_id, username, first_name, last_name, phone_number, date, time, comments, status):
    # Подключаемся к базе данных
    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()

    # Добавляем запись в таблицу
    cursor.execute("""
    INSERT INTO records (user_id, username, first_name, last_name, phone_number, date, time, comments, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, first_name, last_name, phone_number, date, time, comments, status))

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()
