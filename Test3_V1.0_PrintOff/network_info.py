import sqlite3
import socket
import datetime
import requests
import time

class NetworkInfo:
    def __init__(self, db_name="network_info.db"):
        self.db_name = db_name
        self.create_database()

    def create_database(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS network_info (
                                id INTEGER PRIMARY KEY,
                                ip_address TEXT,
                                latitude REAL,
                                longitude REAL,
                                date_time TEXT,
                                connection_status TEXT
                                )''')
            conn.commit()
            conn.close()
        except Exception as e:
            print("Error creating database:", e)

    def get_location(self):
        try:
            response = requests.get("https://ipapi.co/json/")
            data = response.json()
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            return latitude, longitude
        except Exception as e:
            print("Error fetching location:", e)
            return None, None

    def get_datetime(self):
        try:
            now = datetime.datetime.now()
            return now.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            print("Error fetching datetime:", e)
            return None

    def check_connection(self):
        try:
            socket.create_connection(("www.google.com", 80))
            return True
        except Exception as e:
            print("No internet connection:", e)
            return False

    def insert_network_info(self, ip_address, latitude, longitude, date_time, connection_status):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO network_info (ip_address, latitude, longitude, date_time, connection_status) 
                              VALUES (?, ?, ?, ?, ?)''', (ip_address, latitude, longitude, date_time, connection_status))
            conn.commit()
            conn.close()
            print("Network information inserted successfully.")
        except Exception as e:
            print("Error inserting network information:", e)

    def print_individual_elements(self):
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''SELECT ip_address, latitude, longitude, date_time, connection_status FROM network_info 
                              ORDER BY id DESC LIMIT 1''')
            row = cursor.fetchone()
            if row:
                ip_address, latitude, longitude, date_time, connection_status = row
                print("IP Address:", ip_address)
                print("Latitude:", latitude)
                print("Longitude:", longitude)
                
                # Splitting date and time
                date_parts, time_parts = date_time.split(" ")
                year, month, day = date_parts.split("-")
                hour, minute, _ = time_parts.split(":")
                
                print("Date:")
                print("  Year:", year)
                print("  Month:", month)
                print("  Day:", day)
                print("Time:")
                print("  Hour:", hour)
                print("  Minute:", minute)
                
                print("Connection Status:", connection_status)
            else:
                print("No network information found.")
            conn.close()
        except Exception as e:
            print("Error retrieving individual elements:", e)

if __name__ == "__main__":
    network_info = NetworkInfo()
    while True:
        ip_address = socket.gethostbyname(socket.gethostname())
        latitude, longitude = network_info.get_location()
        date_time = network_info.get_datetime()
        connection_status = "Connected" if network_info.check_connection() else "Disconnected"
        network_info.insert_network_info(ip_address, latitude, longitude, date_time, connection_status)
        network_info.print_individual_elements()

        time.sleep(10)
