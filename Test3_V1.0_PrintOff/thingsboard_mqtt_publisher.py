#!/usr/bin/python2
# -*- coding: utf-8 -*-

import sys
import paho.mqtt.client as mqtt
import json
import time
import requests
import sqlite3
import socket
from database_handler import DatabaseHandler  # Assuming this module already exists and works
#from json_checker import check_incoming_json
import json_db_module

class ModemConfigDatabase:
    def __init__(self, db_file='modem_config.db'):
        self.db_file = db_file
        self.create_database()

    def create_database(self):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Create table if it does not exist
            cursor.execute('''CREATE TABLE IF NOT EXISTS modem_parameters (
                                id INTEGER PRIMARY KEY,
                                access_token TEXT,
                                client_id TEXT,
                                user_name TEXT,
                                password TEXT,
                                gsm_modem_mode TEXT,
                                network_type TEXT
                            )''')

            # Check if initial data exists
            cursor.execute('SELECT COUNT(*) FROM modem_parameters')
            if cursor.fetchone()[0] == 0:
                # Insert initial data if the table is empty
                cursor.execute('''INSERT INTO modem_parameters 
                                  (access_token, client_id, user_name, password, gsm_modem_mode, network_type) 
                                  VALUES (?, ?, ?, ?, ?, ?)''', 
                               ('6dNkl093nG4HvksMmYDD', 'pt2gv4dhnol87qgt2lyw', 'qdg6k3nm8quom2u5u4lv', '3thogxnhdanzkje0vuyw', 'esim', 'ethernet'))

            conn.commit()
        except sqlite3.Error as e:
            print("Error creating database: {}".format(e))
        finally:
            conn.close()

    def get_parameter(self, param):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT {} FROM modem_parameters WHERE id = 1'.format(param))
            value = cursor.fetchone()[0]
            return value
        except sqlite3.Error as e:
            print("Error retrieving parameter {}: {}".format(param, e))
            return None
        finally:
            conn.close()

    def update_parameter(self, param, value):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('UPDATE modem_parameters SET {} = ? WHERE id = 1'.format(param), (value,))
            conn.commit()
        except sqlite3.Error as e:
            print("Error updating parameter {} to {}: {}".format(param, value, e))
        finally:
            conn.close()

modem_config_db = ModemConfigDatabase()
access_token = str(modem_config_db.get_parameter('access_token'))

ACCESS_TOKEN = access_token                           
THINGSBOARD_HOST = 'www.dexterhms.com'


# MQTT Callback Functions

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to ThingsBoard successfully")
    else:
        print("Connection failed with code {}".format(rc))

def on_disconnect(client, userdata, rc):
    print("Disconnected from ThingsBoard")

def on_publish(client, userdata, mid):
    print("Message published")

def on_log(client, userdata, level, buf):
    print("log: {}".format(buf))

# Check Ethernet connection using socket
def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53))
        return True
    except Exception as e:
        print("Network check failed: {}".format(e))
        return False

# Setup MQTT Client
client = mqtt.Client()
client.username_pw_set(ACCESS_TOKEN)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_publish = on_publish
client.on_log = on_log


# Function to create a new MQTT client and connect to ThingsBoard
def create_new_mqtt_client():
    client = mqtt.Client()
    client.username_pw_set(ACCESS_TOKEN)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
    client.on_log = on_log
    return client

def connect_to_thingsboard(client):
    while not client.is_connected():
        try:
            client.connect(THINGSBOARD_HOST, 1883, 60)
            client.loop_start()
            while not client.is_connected():
                time.sleep(1)
        except Exception as e:
            print("Failed to connect to ThingsBoard: {}".format(e))
            time.sleep(5)

# Publish Data to ThingsBoard
def publish_data(client, data):
    
    # Convert JSON string to dictionary
    incoming_json_obj = json.dumps(data)
    
    print("----------")
    #print(incoming_json_obj)

    print(incoming_json_obj)

    #parsed_json = json.loads(incoming_json_obj)
    
    # Call the function to check if it matches any stored JSON keys
    #is_match = check_incoming_json(parsed_json) # added 03-10-2024

    #print(is_match)


    # Convert the JSON object to a string for processing if necessary
    #incoming_json = json.dumps(json_obj)  # Convert dict to JSON string
    parsed_json = incoming_json_obj
    
    # Call the function to check this incoming JSON against stored configurations
    #is_matched = json_db_module.check_incoming_json(incoming_json)
    is_match = json_db_module.check_incoming_json(parsed_json)  #added 05-10-2024

    print(is_match)

    # Display the result
    #if is_matched:
    #    print("Match found with stored JSON configuration.")
    #else:
    #    print("No matching configuration found.")


    # Use the result for further conditional checking
    if is_match:
        print("Matching configuration found in the database.")
        telemetry_topic = 'v1/devices/me/attributes'
        #ret= client1.publish("v1/devices/me/attribute",attributes_json)
        result = client.publish(telemetry_topic, json.dumps(data))
        result.wait_for_publish()
        print("Data sent to ThingsBoard: ", str(data))
        
    else:
        print("No matching configuration found.")
        telemetry_topic = 'v1/devices/me/telemetry'
        #telemetry_topic = 'v1/devices/me/attributes'
        result = client.publish(telemetry_topic, json.dumps(data))
        #ret= client1.publish("v1/devices/me/attributes",data)             #topic-v1/devices/me/telemetry
        result.wait_for_publish()
        print("Data sent to ThingsBoard: ", str(data))
        
    
#    result = client.publish(telemetry_topic, json.dumps(data))
#    result.wait_for_publish()
#    print("Data sent to ThingsBoard: ", str(data))


class ChildProgram:
    def __init__(self, db_handler):
        self.db_handler = db_handler
        self.client = None
        self.connected = False

    def initialize_connection(self):
        self.client = create_new_mqtt_client()
        connect_to_thingsboard(self.client)
        self.connected = True
        print("A new MQTT client was initialized and connected to ThingsBoard.")

    def send_to_cloud(self, data):
        if is_connected():
            if not self.connected:  # Only attempt to reconnect if we're not already connected
                self.initialize_connection()
            publish_data(self.client, json.loads(data))

    def run(self):
        while True:
            if is_connected():
                if not self.connected:  # Reinitialize the connection if it was disconnected for a long time
                    self.initialize_connection()

                row_id, json_str = self.db_handler.get_json_string()
                if json_str:
                    self.send_to_cloud(json_str)
                    self.db_handler.mark_as_sent(row_id)
                else:
                    print("No new data to send. Checking again in 5 seconds.")
            else:
                self.connected = False  # Mark the client as disconnected
                print("No network connection, retrying...")
                if self.client:
                    self.client.loop_stop()  # Stop the loop and disconnect the current client
                    self.client.disconnect()  # Properly disconnect the client
                    self.client = None  # Set the client to None so a new one will be created later
            time.sleep(5)


if __name__ == "__main__":
    db_handler = DatabaseHandler()
    program = ChildProgram(db_handler)
    network_type = modem_config_db.get_parameter('network_type')
    print("Current Network Type:", str(network_type))
    
    try:
        if network_type == 'ethernet':
            program.run()
        else:
            pass
    except KeyboardInterrupt:
        if program.client:
            program.client.loop_stop()
            program.client.disconnect()
