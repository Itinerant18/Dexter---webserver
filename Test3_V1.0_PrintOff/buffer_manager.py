# buffer_manager.py

import sqlite3

# Initialize the SQLite database and create the buffer table
def init_db(db_name="/home/pi/Test3/buffer.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS buffer 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       json_object TEXT)''')
    conn.commit()
    conn.close()

# Insert JSON object into the SQLite buffer
def insert_json_to_db(json_data, db_name="/home/pi/Test3/buffer.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO buffer (json_object) VALUES (?)", (json_data,))
    conn.commit()
    conn.close()

# Retrieve and delete the oldest JSON object from the buffer
def get_and_delete_json_from_db(db_name="/home/pi/Test3/buffer.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT id, json_object FROM buffer LIMIT 1")
    record = cursor.fetchone()
    if record:
        cursor.execute("DELETE FROM buffer WHERE id=?", (record[0],))
    conn.commit()
    conn.close()
    return record[1] if record else None
