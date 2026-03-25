import sqlite3
import os

# Database setup
db_path = "/home/pi/Test3/logical_params_active_integration.db"

def initialize_database():
    try:
        # Create database file if it doesn't exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                value INTEGER NOT NULL CHECK (value IN (0, 1))
            )
        ''')

        # Insert default values if the table is empty
        cursor.execute("SELECT COUNT(*) FROM parameters")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO parameters (name, value) VALUES (?, ?)",
                [
                    ("active_integration_hikvision_nvr", 0), 
                    ("active_integration_hikvision_biometric", 0), 
                    ("active_integration_dahua_nvr", 0)
                ]
            )

        conn.commit()
    except sqlite3.Error as e:
        print("Error initializing database: {}".format(e))
    finally:
        conn.close()

def set_parameter(param_name, param_value):
    if param_value not in (0, 1):
        print("Error: Parameter value must be 0 (False) or 1 (True).")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE parameters SET value = ? WHERE name = ?",
            (param_value, param_name)
        )

        if cursor.rowcount == 0:
            print("Error: Parameter '{}' does not exist.".format(param_name))
        else:
            conn.commit()
            print("Parameter '{}' set to {}.".format(param_name, param_value))
    except sqlite3.Error as e:
        print("Error setting parameter: {}".format(e))
    finally:
        conn.close()

def get_parameter(param_name):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT value FROM parameters WHERE name = ?",
            (param_name,)
        )
        row = cursor.fetchone()

        if row is None:
            print("Error: Parameter '{}' does not exist.".format(param_name))
            return None
        else:
            return row[0]
    except sqlite3.Error as e:
        print("Error getting parameter: {}".format(e))
        return None
    finally:
        conn.close()

# To use this module, import it in another Python script.
if __name__ == "__main__":
    # Initialize database
    initialize_database()

    # Example usage
    print("Setting parameters...")
    set_parameter("active_integration_hikvision_nvr", 1)
    set_parameter("active_integration_hikvision_biometric", 0)

    print("Getting parameters...")
    print("active_integration_hikvision_nvr:", get_parameter("active_integration_hikvision_nvr"))
    print("active_integration_hikvision_biometric:", get_parameter("active_integration_hikvision_biometric"))
    print("active_integration_dahua_nvr:", get_parameter("active_integration_dahua_nvr"))
