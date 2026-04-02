import sqlite3
import socket
import requests
import json

# Access the command-line arguments
# sys.argv[0] is the script name
# sys.argv[1:] are the arguments passed to the script
json_params = sys.argv[1]
#print(json_params)

# Parse the JSON parameters
json_object = json.loads(json_params)

# Use the parameters as needed
#print(json_object)

json_formatted_str = json.dumps(json_object, indent=2)


def check_internet_connection():
    try:
        # Attempt to create a connection to Google's public DNS server (8.8.8.8) on port 53
        socket.create_connection(('8.8.8.8', 53), timeout=5)
        return True
    except socket.error:
        return False


def get_current_location():
    try:
        response = requests.get('https://ipinfo.io/json')
        data = response.json()
        coordinates = data.get('loc').split(',')
        latitude = coordinates[0]
        longitude = coordinates[1]
        return float(latitude), float(longitude)
    except Exception as e:
        print("Error occurred:", e)
        return None, None

# Connect to SQLite database (creates new database if it doesn't exist)
conn = sqlite3.connect('parameters.db')

# Create a cursor object to execute SQL queries
cursor = conn.cursor()

# Create a table to store parameters
cursor.execute('''CREATE TABLE IF NOT EXISTS parameters
                (id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                value REAL)''')

# Function to insert or update parameters
def insert_or_update_parameter(name, value):
    try:
        cursor.execute('''INSERT INTO parameters (name, value)
                        VALUES (?, ?)''', (name, value))
    except sqlite3.IntegrityError:  # Unique constraint violation, update instead
        cursor.execute('''UPDATE parameters
                        SET value = ?
                        WHERE name = ?''', (value, name))
    conn.commit()

# Insert or update parameters
#insert_or_update_parameter('parameter1', 10)
#insert_or_update_parameter('parameter2', 20)
#insert_or_update_parameter('parameter1', 15)  # Update parameter1


if check_internet_connection():
    status = 1
else:
    status = 0

# Update parameter1
insert_or_update_parameter('internet_connection_status', (status))     # Update parameter1

try:
    latitude, longitude = get_current_location()
    if latitude is not None and longitude is not None:
        #print("Current Latitude:", latitude)
        #print("Current Longitude:", longitude)
        insert_or_update_parameter('Latitude', (latitude))     # Update parameter1
        insert_or_update_parameter('Longitude', (longitude))     # Update parameter1
    else:
        print("Unable to retrieve current location.")
except:
    pass

# Fetch all parameters from the table
cursor.execute('''SELECT * FROM parameters''')
parameters = cursor.fetchall()

# Create arrays to store individual parameter names and values
parameter_names = []
parameter_values = []

# Populate arrays with individual parameter names and values
for parameter in parameters:
    parameter_names.append(parameter[1])  # Name is at index 1
    parameter_values.append(parameter[2])  # Value is at index 2

# Print individual parameter names and values
#print("Parameter Names:", parameter_names)
#print("Parameter Values:", parameter_values)

# Close cursor and connection
cursor.close()
conn.close()
