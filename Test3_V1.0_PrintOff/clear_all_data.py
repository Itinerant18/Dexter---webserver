import sqlite3


def clear_all_data(db_path):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get a list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Clear data from each table
        for table_name in tables:
            cursor.execute("DELETE FROM {}".format(table_name[0]))
            print("Cleared data from table: {}".format(table_name[0]))

        # Commit the changes
        conn.commit()
        print("All table data cleared, but table structures are intact.")

    except sqlite3.Error as e:
        print("Error occurred:", e)

    finally:
        # Close the database connection
        if conn:
            conn.close()

# Example usage
database_path = '/home/pi/Test3/payloads.db'
clear_all_data(database_path)
database_path = '/home/pi/Test3/buffer.db'
clear_all_data(database_path)
