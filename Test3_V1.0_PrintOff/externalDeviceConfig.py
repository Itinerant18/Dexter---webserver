#!/usr/bin/python2
import sqlite3

# Database location
#DB_PATH = "/path/to/device_config.db"
DB_PATH = "device_config.db"

def create_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS device_parameters (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_type TEXT NOT NULL,
                        ip_address TEXT NOT NULL,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        port INTEGER NOT NULL)''')
    conn.commit()
    conn.close()

def add_device(device_type, ip_address, username, password, port):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO device_parameters (device_type, ip_address, username, password, port) VALUES (?, ?, ?, ?, ?)", 
                   (device_type, ip_address, username, password, port))
    conn.commit()
    conn.close()
    print("Device added successfully!")

def delete_device(device_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM device_parameters WHERE id=?", (device_id,))
    conn.commit()
    conn.close()
    print("Device deleted successfully!")

def modify_device(device_id, device_type, ip_address, username, password, port):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''UPDATE device_parameters SET device_type=?, ip_address=?, username=?, password=?, port=? WHERE id=?''',
                   (device_type, ip_address, username, password, port, device_id))
    conn.commit()
    conn.close()
    print("Device updated successfully!")

def list_devices():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM device_parameters")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        print("ID: {}, Device Type: {}, IP: {}, Username: {}, Port: {}".format(row[0], row[1], row[2], row[3], row[5]))

def user_interface():
    create_table()
    while True:
        print("1. Add Device")
        print("2. Delete Device")
        print("3. Modify Device")
        print("4. List Devices")
        print("5. Exit")
        choice = int(raw_input("Enter your choice: "))
        if choice == 1:
            device_type = raw_input("Enter Device Type (e.g., Hikvision NVR, Dahua NVR, Biometric Device): ")
            ip_address = raw_input("Enter IP Address: ")
            username = raw_input("Enter Username: ")
            password = raw_input("Enter Password: ")
            port = int(raw_input("Enter Port: "))
            add_device(device_type, ip_address, username, password, port)
        elif choice == 2:
            device_id = int(raw_input("Enter Device ID to delete: "))
            delete_device(device_id)
        elif choice == 3:
            device_id = int(raw_input("Enter Device ID to modify: "))
            device_type = raw_input("Enter Device Type (e.g., Hikvision NVR, Dahua NVR, Biometric Device): ")
            ip_address = raw_input("Enter IP Address: ")
            username = raw_input("Enter Username: ")
            password = raw_input("Enter Password: ")
            port = int(raw_input("Enter Port: "))
            modify_device(device_id, device_type, ip_address, username, password, port)
        elif choice == 4:
            list_devices()
        elif choice == 5:
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    user_interface()
