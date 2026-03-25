#!/usr/bin/python2
import sqlite3
import json

#DB_PATH = "/path/to/device_config.db"
DB_PATH = "/home/pi/Test3/device_config.db"

def get_device_parameters_old(device_type):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM device_parameters WHERE device_type=?", (device_type,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def create_table():
    """Create the device_parameters table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS device_parameters (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        device_type TEXT NOT NULL,
                        ip_address TEXT NOT NULL,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        port INTEGER NOT NULL,
                        camera_ip TEXT)''')  # camera_ip column as JSON string
    conn.commit()
    conn.close()

def add_device(device_type, ip_address, username, password, port, camera_ip_list=None):
    """Add a new device to the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    camera_ip_json = json.dumps(camera_ip_list) if camera_ip_list else None
    cursor.execute('''INSERT INTO device_parameters 
                      (device_type, ip_address, username, password, port, camera_ip) 
                      VALUES (?, ?, ?, ?, ?, ?)''', 
                   (device_type, ip_address, username, password, port, camera_ip_json))
    conn.commit()
    conn.close()

def update_camera_ips_by_type(device_type, camera_ip_list):
    """Update the camera_ip field for all entries of the given device type."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    camera_ip_json = json.dumps(camera_ip_list)
    cursor.execute("UPDATE device_parameters SET camera_ip=? WHERE device_type=?", 
                   (camera_ip_json, device_type))
    conn.commit()
    conn.close()

def get_camera_ips_by_type(device_type):
    """Retrieve the stored camera IP list for a given device type."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT camera_ip FROM device_parameters WHERE device_type=?", (device_type,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0]:
        try:
            return json.loads(result[0])
        except Exception as e:
            print "[ERROR] Failed to parse camera IPs JSON:", e
    return []



def delete_device(device_id):
    """Delete a device from the database by ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM device_parameters WHERE id=?", (device_id,))
    conn.commit()
    conn.close()

def modify_device(device_id, device_type, ip_address, username, password, port, camera_ip_list=None):
    """Modify an existing device's details in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    camera_ip_json = json.dumps(camera_ip_list) if camera_ip_list else None
    cursor.execute('''UPDATE device_parameters 
                      SET device_type=?, ip_address=?, username=?, password=?, port=?, camera_ip=? 
                      WHERE id=?''',
                   (device_type, ip_address, username, password, port, camera_ip_json, device_id))
    conn.commit()
    conn.close()

def modify_device_field(device_id, field, new_value):
    """Modify a specific field of a device."""
    if field not in ["device_type", "ip_address", "username", "password", "port", "camera_ip"]:
        raise ValueError("Invalid field name.")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if field == "camera_ip" and isinstance(new_value, list):
        new_value = json.dumps(new_value)
    query = "UPDATE device_parameters SET {} = ? WHERE id = ?".format(field)
    cursor.execute(query, (new_value, device_id))
    conn.commit()
    conn.close()

def list_devices():
    """List all devices in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM device_parameters")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_device_parameters(device_type):
    """Retrieve all devices of a specific type."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM device_parameters WHERE device_type=?", (device_type,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def modify_device_field_by_type(device_type, field, new_value):
    """
    Modify a specific field of all devices with the specified device_type.

    :param device_type: The type of device to filter by.
    :param field: The field to update (e.g., "password", "ip_address").
    :param new_value: The new value for the specified field.
    """
    #if field not in ["device_type", "ip_address", "username", "password", "port", "camera_ip"]:
    #    raise ValueError("Invalid field name.")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if field == "camera_ip" and isinstance(new_value, list):
        new_value = json.dumps(new_value)
    query = "UPDATE device_parameters SET {} = ? WHERE device_type = ?".format(field)
    cursor.execute(query, (new_value, device_type))
    conn.commit()
    conn.close()
    #print(f"{field} updated successfully for all devices of type '{device_type}'.")


# Ensure the table is created when the module is first used
#create_table()


#if __name__ == "__main__":
    # Example usage: Get all parameters for a specific device type
    #create_table()
    #device_type = raw_input("Enter the Device Type to fetch (e.g., Hikvision NVR): ")
    #devices = get_device_parameters(device_type)
    #if devices:
    #    for device in devices:
    #        print("ID: {}, Device Type: {}, IP: {}, Username: {}, Port: {}, camera_ip: {}".format(device[0], device[1], device[2], device[3], device[5], device[6]))
    #else:
    #    print("No devices found for the given device type.")
