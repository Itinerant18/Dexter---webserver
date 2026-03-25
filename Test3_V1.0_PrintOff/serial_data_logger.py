# -*- coding: utf-8 -*-
# !/usr/local/bin/python

# serial_data_logger.py

import serial
import time
import json
import sqlite3
import threading
import os
import sys


from buffer_manager import insert_json_to_db

class SoftwareWatchdog:
    def __init__(self, timeout=600):
        """
        Initialize the software watchdog.
        :param timeout: Time in seconds before triggering a reset if not fed.
        """
        self.timeout = timeout
        self.last_reset = time.time()
        self._running = True
        self.thread = threading.Thread(target=self._watchdog_loop)
        self.thread.setDaemon(True)  # Set daemon mode for Python 2 compatibility
        self.thread.start()

    def _watchdog_loop(self):
        """ Watchdog monitoring loop that checks if the timeout is exceeded. """
        while self._running:
            if time.time() - self.last_reset > self.timeout:
                print "Watchdog timeout! Restarting software..."
                self._restart_program()
            time.sleep(1)

    def reset(self):
        """ Reset the watchdog timer to prevent restart. """
        self.last_reset = time.time()
        #print "Watchdog reset at:", time.strftime('%Y-%m-%d %H:%M:%S')  # Debugging print

    def stop(self):
        """ Stop the watchdog timer. """
        self._running = False
        self.thread.join()
  
#    def _restart_program(self):
#       """ Restart the script using OS system call. """
#       self._running = False  # Stop watchdog loop
       #self.thread.join()  # Ensure the thread terminates
#       python = sys.executable if sys.executable else "/usr/bin/python2"
#       os.execl(python, python, *sys.argv)

    def _restart_program(self):
        """ Restart the script using OS system call and log to database. """
        self._running = False  # Stop watchdog loop

        # Prepare the log message
        log_data = {
            "watchdog_log": [
                {
                    "Module Reboot": "Power Status",
                    "timestamp": datetime.now().strftime("%d-%m-%y %H:%M:%S")
                }
            ]
        }

        # Convert to JSON and insert into DB
        attributes_json = json.dumps(log_data)
        try:
            insert_json_to_db(attributes_json)
        except Exception as e:
            print("Failed to insert watchdog log into database:", e)

        print "Watchdog timeout! Restarting software..."
    
        # Restart the script
        python = sys.executable if sys.executable else "/usr/bin/python2"
        os.execl(python, python, *sys.argv)
    
# Initialize software watchdog with 600-second timeout
watchdog = SoftwareWatchdog(timeout=600)


class ControllerDatabaseManager:
    def __init__(self, db_name='parameters.db'):
        self.db_name = db_name

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            return self.conn
        except sqlite3.Error as e:
            print("Error connecting to database:", e)
            return None

    def create_table(self):
        conn = self.connect()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute('''CREATE TABLE IF NOT EXISTS parameters (
                    id INTEGER PRIMARY KEY,
                    panel_current REAL,
                    battery_voltage REAL,
                    ac_voltage REAL,
                    lithium_ion_bat_volt_sense REAL
                )''')
                conn.commit()
            except sqlite3.Error as e:
                print("Error creating table:", e)
            finally:
                conn.close()

    def insert_or_update_parameters(self, panel_current, battery_voltage, ac_voltage, lithium_ion_bat_volt_sense):
        conn = self.connect()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute('''SELECT COUNT(*) FROM parameters''')
                count = cursor.fetchone()[0]

                if count > 0:
                    cursor.execute('''UPDATE parameters
                                      SET panel_current = ?, battery_voltage = ?, ac_voltage = ?, lithium_ion_bat_volt_sense = ?
                                      WHERE id = 1''', (panel_current, battery_voltage, ac_voltage, lithium_ion_bat_volt_sense))
#                    print("Parameters updated successfully.")
                else:
                    cursor.execute('''INSERT INTO parameters (panel_current, battery_voltage, ac_voltage, lithium_ion_bat_volt_sense)
                                      VALUES (?, ?, ?, ?)''', (panel_current, battery_voltage, ac_voltage, lithium_ion_bat_volt_sense))
#                    print("Parameters inserted successfully.")
                conn.commit()
            except sqlite3.Error as e:
                print("Error inserting or updating parameters:", e)
            finally:
                conn.close()

    def fetch_and_print_parameters(self):
        conn = self.connect()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute('''SELECT * FROM parameters''')
                rows = cursor.fetchall()
#                for row in rows:
#                    print("ID:", row[0])
#                    print("Panel Current:", row[1])
#                    print("Battery Voltage:", row[2])
#                    print("AC Voltage:", row[3])
#                    print("Lithium-ion Battery Voltage Sense:", row[4])
            except sqlite3.Error as e:
                print("Error fetching parameters:", e)
            finally:
                conn.close()

    def get_panel_current(self):
        conn = self.connect()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute('''SELECT panel_current FROM parameters WHERE id = 1''')
                result = cursor.fetchone()
                if result:
                    return result[0]
                return None
            except sqlite3.Error as e:
                print("Error getting panel current:", e)
                return None
            finally:
                conn.close()

    def get_battery_voltage(self):
        conn = self.connect()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute('''SELECT battery_voltage FROM parameters WHERE id = 1''')
                result = cursor.fetchone()
                if result:
                    return result[0]
                return None
            except sqlite3.Error as e:
                print("Error getting battery voltage:", e)
                return None
            finally:
                conn.close()

    def get_ac_voltage(self):
        conn = self.connect()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute('''SELECT ac_voltage FROM parameters WHERE id = 1''')
                result = cursor.fetchone()
                if result:
                    return result[0]
                return None
            except sqlite3.Error as e:
                print("Error getting AC voltage:", e)
                return None
            finally:
                conn.close()

    def get_lithium_ion_bat_volt_sense(self):
        conn = self.connect()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute('''SELECT lithium_ion_bat_volt_sense FROM parameters WHERE id = 1''')
                result = cursor.fetchone()
                if result:
                    return result[0]
                return None
            except sqlite3.Error as e:
                print("Error getting lithium-ion battery voltage sense:", e)
                return None
            finally:
                conn.close()

def setup_serial_connection(port, baudrate, timeout):
    try:
        ser = serial.Serial(port, baudrate=baudrate, timeout=timeout)
        return ser
    except serial.SerialException as e:
        print("Error opening serial port:", e)
        return None

def initVariable():

    panel_current = 0.0
    battery_voltage = 0.0
    ac_voltage = 0.0
    lithium_ion_bat_volt_sense = 0.0
 
    controller_db_manager.insert_or_update_parameters(panel_current, battery_voltage, ac_voltage, lithium_ion_bat_volt_sense)
    controller_db_manager.fetch_and_print_parameters()

def main():
    while True:
        ser = setup_serial_connection("/dev/ttyUSB0", 9600, 1)
        if ser is None:
            print("Failed to connect to serial port. Retrying in 5 seconds...")
            time.sleep(5)
            continue

#        controller_db_manager = ControllerDatabaseManager()
#        controller_db_manager.create_table()

        buffer = ""
        while True:
            try:
                data = ser.read(100)
                if data:
                    buffer += data.decode('utf-8', errors='ignore')
                    while True:
                        start_index = buffer.find('{')
                        end_index = buffer.find('}')
                        if start_index != -1 and end_index != -1 and end_index > start_index:
                            json_string = buffer[start_index:end_index+1]
                            buffer = buffer[end_index+1:]

                            try:
                                parsed_json = json.loads(json_string)

                                panel_current = parsed_json.get("panel_current")
                                battery_voltage = parsed_json.get("battery_voltage")
                                ac_voltage = parsed_json.get("ac_voltage")
                                lithium_ion_bat_volt_sense = parsed_json.get("lithium_ion_bat_volt_sense")

                                if panel_current is not None and battery_voltage is not None:
#                                    print("Panel Current:", panel_current)
#                                    print("Battery Voltage:", battery_voltage)
#                                    print("AC Voltage:", ac_voltage)
#                                    print("Lithium-ion Battery Voltage Sense:", lithium_ion_bat_volt_sense)

                                    controller_db_manager.insert_or_update_parameters(panel_current, battery_voltage, ac_voltage, lithium_ion_bat_volt_sense)
                                    controller_db_manager.fetch_and_print_parameters()
                                else:
                                    print("Invalid JSON message format.")
                            except ValueError:
                                print("Failed to decode JSON from message.")
                        else:
                            break
            except serial.SerialException as e:
                print("Serial communication error:", e)
                break

        ser.close()

controller_db_manager = ControllerDatabaseManager()
controller_db_manager.create_table()    
if __name__ == '__main__':
    initVariable()
    main()
    watchdog.reset()  # Reset watchdog after 10min
    time.sleep(1)
