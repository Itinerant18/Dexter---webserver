# -*- coding: utf-8 -*-
# !/usr/local/bin/python

import threading
import time
import os
import sys
import chardet
import json_db_module


from buffer_manager import insert_json_to_db

class SoftwareWatchdog:
    def __init__(self, timeout=300):
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
#        """ Restart the script using OS system call. """
#        self._running = False  # Stop watchdog loop
        #self.thread.join()  # Ensure the thread terminates
#        python = sys.executable if sys.executable else "/usr/bin/python2"
#        os.execl(python, python, *sys.argv)
        
    def _restart_program(self):
        """ Restart the script using OS system call and log to database. """
        self._running = False  # Stop watchdog loop

        # Prepare the log message
        log_data = {
            "watchdog_log": [
                {
                    "Module Reboot": "eSIM",
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
    
# Initialize software watchdog with 10-second timeout
watchdog = SoftwareWatchdog(timeout=300)


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
                                network_type TEXT,
                                device_name TEXT
                            )''')

            # Check if initial data exists
            cursor.execute('SELECT COUNT(*) FROM modem_parameters')
            if cursor.fetchone()[0] == 0:
                # Insert initial data if the table is empty
                cursor.execute('''INSERT INTO modem_parameters 
                                  (access_token, client_id, user_name, password, gsm_modem_mode, network_type, device_name) 
                                  VALUES (?, ?, ?, ?, ?, ?)''', 
                               ('6dNkl093nG4HvksMmYDD', 'pt2gv4dhnol87qgt2lyw', 'qdg6k3nm8quom2u5u4lv', '3thogxnhdanzkje0vuyw', 'esim', 'ethernet', 'dexter'))

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

class State:
    """Base state class.
    
    Attributes:
        name (str): The name of the state.
        params (dict): Parameters passed to the state.
    """
    def __init__(self, **kwargs):
        """Initialize the state with optional parameters."""
        self.name = self.__class__.__name__
        self.params = kwargs

    def on_event(self, event):
        """Handle events that are delegated to this State.
        
        Args:
            event (str): The event to handle.
            
        Returns:
            State: The next state after handling the event.
        """
        pass

    def __str__(self):
        """Return the name and parameters of the state."""
        return self.name + " with params: " + str(self.params)

class ErrorState(State):
    """State for handling errors."""
    def on_event(self, event):
        print "Error state: cannot handle events."
        return ModemSetUp()

class InitializeModem(State):
    """State for initializing the modem."""
    def on_event(self, event):
        try:
            print "Initializing modem...1"
            if event == 'network_check':
                initialize_device()
                return CheckNetworkStatus(**self.params)
        except Exception as e:
            print "Error in InitializeModem: %s" % str(e)
            return ErrorState()
        return self

class CheckNetworkStatus(State):
    """State for checking network status."""
    def on_event(self, event):
        try:
            print "Checking network status..."
            if event == 'signal_strength':
       #         main(None, str(2))
                main(None, str(6))
                return CheckSignalStrength(**self.params)
        except Exception as e:
            print "Error in CheckNetworkStatus: %s" % str(e)
            return ErrorState()
        return self

class CheckSignalStrength(State):
    """State for checking signal strength."""
    def on_event(self, event):
        try:
            print "Checking signal strength..."
            if event == 'send_payload':
                row_id, json_str = db_handler.get_json_string()
                if json_str:
                    main(child_program.send_to_cloud(json_str), str(1))
                    child_program.send_to_cloud(json_str)
                    db_handler.mark_as_failed(row_id)  # Mark as Failed always
                else:
                    print "No new data to send. Checking again in 5 seconds."
                
                return SendPayload(**self.params)
        except Exception as e:
            print "Error in CheckSignalStrength: %s" % str(e)
            return ErrorState()
        return self

class SendPayload(State):
    """State for sending payload to the cloud."""
    def on_event(self, event):
        try:
            print "Sending payload to the cloud..."
            if event == 'confirm_delivery':
                return ConfirmDelivery(**self.params)
        except Exception as e:
            print "Error in SendPayload: %s" % str(e)
            return ErrorState()
        return self

class ConfirmDelivery(State):
    """State for confirming payload delivery."""
    def on_event(self, event):
        try:
            print "Confirming payload delivery..."
            if event == 'network_check':
                return CheckNetworkStatus(**self.params)
            elif event == 'terminate':
                return TerminateConnection(**self.params)
        except Exception as e:
            print "Error in ConfirmDelivery: %s" % str(e)
            return ErrorState()
        return self

class TerminateConnection(State):
    """State for terminating the connection."""
    def on_event(self, event):
        try:
            print "Terminating the connection..."
            if event == 'initialize':
                return InitializeModem(**self.params)
        except Exception as e:
            print "Error in TerminateConnection: %s" % str(e)
            return ErrorState()
        return self

class ChangeOperator(State):
    """State for changing the operator."""
    def on_event(self, event, **kwargs):
        try:
            new_operator_id = kwargs.get('operator_id', None)
            if new_operator_id:
                print "Changing operator to ID:", new_operator_id
                # Here you would add the logic to change the operator.
                # For this example, we are just simulating a successful change.
                self.params['operator_id'] = new_operator_id
                print "Operator changed successfully."
                return CheckNetworkStatus(**self.params)
        except Exception as e:
            print "Error in ChangeOperator: %s" % str(e)
            return ErrorState()
        return self

class ModemSetUp(State):
    """State for modem setup."""
    def on_event(self, event):
        try:
            print "Setting up modem..."
            time.sleep(60)
            reset_device()
            time.sleep(30)
            main(None, str(2))
            switch_to_esim_sim()
            # switch_to_physical_sim()
            time.sleep(30)
            
            # After setup, decide where to go next, for example, check network status
            return CheckNetworkStatus(**self.params)
        except Exception as e:
            print "Error in ModemSetUp: %s" % str(e)
            return ErrorState()
        return self

class Context:
    """Context class for maintaining state and handling events."""
    def __init__(self, initial_state, **kwargs):
        self.state = initial_state(**kwargs)

    def on_event(self, event):
        self.state = self.state.on_event(event)

    def __str__(self):
        return str(self.state)



import serial
import time
import sys
import json

import paho.mqtt.client as paho  		    #mqtt library
import os
import time
import datetime
from datetime import datetime
from datetime import date
import requests
import sqlite3

from database_handler import DatabaseHandler

#sudo raspi-config

param1 = 0
param2 = '1'

#param1 = sys.argv[1]
#param2 = sys.argv[2]

attempts = 0


class CavliRunningStatusDatabase:
    def __init__(self, db_name='cavliRunningParam.db'):
        self.db_name = db_name
        self.initialize_database()

    def initialize_database(self):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS cavliRunningParam
                         (latitude REAL, longitude REAL, dataSending TEXT, modemStatus TEXT, serviceProvider TEXT, simSwap TEXT, IMEI TEXT, SerialNumber TEXT)''')
            # Inserting default values during initialization
            c.execute('''INSERT INTO cavliRunningParam VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (None, None, None, None, None, None, None, None))
            conn.commit()
        except sqlite3.Error as e:
            print("Error initializing database:", e)
        finally:
            if conn:
                conn.close()

    def update_cavli_running_parameters(self, column, value):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''UPDATE cavliRunningParam SET {} = ?'''.format(column), (value,))
            conn.commit()
        except sqlite3.Error as e:
            print("Error updating parameters:", e)
        finally:
            if conn:
                conn.close()

    def retrieve_cavli_running_parameters(self, column):
        try:
            conn = sqlite3.connect(self.db_name)
            c = conn.cursor()
            c.execute('''SELECT {} FROM cavliRunningParam'''.format(column))
            result = c.fetchone()
            return result[0] if result else None
        except sqlite3.Error as e:
            print("Error retrieving parameters:", e)
        finally:
            if conn:
                conn.close()


    # Methods to retrieve individual parameters
    def get_latitude(self):
        return self.retrieve_cavli_running_parameters('latitude')

    def get_longitude(self):
        return self.retrieve_cavli_running_parameters('longitude')

    def get_data_sending(self):
        return self.retrieve_cavli_running_parameters('dataSending')

    def get_modem_status(self):
        return self.retrieve_cavli_running_parameters('modemStatus')

    def get_service_provider(self):
        return self.retrieve_cavli_running_parameters('serviceProvider')

    def get_sim_swap(self):
        return self.retrieve_cavli_running_parameters('simSwap')

    def get_IMEI(self):
        return self.retrieve_cavli_running_parameters('IMEI')
    
    def get_SerialNumber(self):
        return self.retrieve_cavli_running_parameters('SerialNumber')
                

class SerialCommander(object):
    def __init__(self, port='/dev/ttyS0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def initialize_serial(self):
        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        return self.ser

    def test_serial_connection(self):
        return self.ser.isOpen() if self.ser else False

    def close_serial(self):
        if self.ser:
            self.ser.close()

    def send_command(self, command, expected_response, timeout=1):
        if not self.ser:
            return False

        print(command) 
        self.ser.write(command + '\r\n')  # Send the command
        
        self.ser.timeout = timeout
        response = self.ser.read_until(expected_response.encode())  # Read until expected response or timeout
        #print(response.decode().strip())

        if expected_response in response:
            print("Expected response received:", expected_response)
            return True
        else:
            print("Unexpected response received:", response)
            return False



    def send_command_and_get_response(self, command, expected_response=None, timeout=1):
        if not self.ser:
            return False, None  # Return False and None response if serial connection is not established

        print command
        self.ser.write(command.encode('utf-8') + '\r\n')  # Send the command with UTF-8 encoding

        self.ser.timeout = timeout

        if expected_response is not None:
            response = self.ser.read_until(expected_response.encode('utf-8'))  # Read until expected response or timeout
            try:
                decoded_response = response.decode('utf-8').strip()
                print decoded_response
            except UnicodeDecodeError as e:
                print "Decoding error:", e
                return False, None
        else:
            response = self.ser.read_until()  # Read until timeout
            try:
                decoded_response = response.decode('utf-8').strip()
            except UnicodeDecodeError as e:
                print "Decoding error:", e
                return False, None

        if expected_response is not None:
            if expected_response in decoded_response:
                print "Expected response received:", expected_response
                return True, decoded_response  # Return True and the response
            else:
                print "Unexpected response received:", decoded_response
                return False, decoded_response  # Return False and the response
        else:
            # No expected response, just return the response
            return True, decoded_response


    def send_command_and_get_response_non_ascii_format(self, command, expected_response=None, timeout=1):
        if not self.ser:
            return False, None  # Return False and None response if serial connection is not established

        print(command) 
        self.ser.write(command.encode() + b'\r\n')  # Send the command
        
        self.ser.timeout = timeout

        if expected_response is not None:
            response = self.ser.read_until(expected_response.encode())  # Read until expected response or timeout
            print(response.decode().strip())
        else:
            
            pass

        if expected_response is not None:
            if expected_response in response:
                print("Expected response received:", expected_response)
                return True, response.decode().strip()  # Return True and the response
            else:
                print("Unexpected response received:", response)
                return False, response.decode().strip()  # Return False and the response
        else:
            # No expected response, just return the response
            #return True, response.decode().strip()
            return True

    def send_command_get_response_with_encoding(self, command, expected_response=None, timeout=1, encoding='utf-8'):
        if not self.ser:
            return False, None  # Return False and None response if serial connection is not established

        print(command)
        try:
            self.ser.write(command.encode(encoding) + b'\r\n')  # Send the command with specified encoding
        except UnicodeEncodeError as e:
            print("Encoding error:", e)
            return False, None

            self.ser.timeout = timeout

        if expected_response is not None:
            try:
                response = self.ser.read_until(expected_response.encode(encoding))  # Read until expected response or timeout
                decoded_response = response.decode(encoding).strip()
                print(decoded_response)
            except (UnicodeDecodeError, UnicodeEncodeError) as e:
                print("Decoding or Encoding error:", e)
                return False, None
        else:
            try:
                response = self.ser.read_until()  # Read until timeout
                decoded_response = response.decode(encoding).strip()
            except (UnicodeDecodeError, UnicodeEncodeError) as e:
                print("Decoding or Encoding error:", e)
                return False, None

        if expected_response is not None:
            if expected_response in decoded_response:
                print("Expected response received:", expected_response)
                return True, decoded_response  # Return True and the response
            else:
                print("Unexpected response received:", decoded_response)
                return False, decoded_response  # Return False and the response
        else:
            # No expected response, just return the response
            return True, decoded_response

    def send_command_and_print_response(self, command, timeout=1):
        success, response = self.read_serial_response(command, timeout)
        if success:
            print(response)
        return success, response  

    def read_serial_response(self, command, timeout=1):
        if not self.ser:
            return False, None  # Return False and None response if serial connection is not established

        self.ser.write(command.encode('utf-8') + b'\r\n')  # Send the command with UTF-8 encoding

        self.ser.timeout = timeout

        response = b''
        while True:
            part = self.ser.read(self.ser.in_waiting or 1)
            if not part:
                break
            response += part
            time.sleep(0.1)  # Give time for more data to arrive

        try:
            decoded_response = response.decode('utf-8').strip()
        except UnicodeDecodeError:
            try:
                decoded_response = response.decode('latin-1').strip()
            except UnicodeDecodeError as e:
                print("Decoding error:", e)
                return False, None

        return True, decoded_response


    def clear_serial_port(self):
        try:
            # Flush input and output buffers
            self.ser.flushInput()
            self.ser.flushOutput()
            #print("Serial port cleared successfully.")
        except Exception as e:
            print("Error: ", e)



cavli_database = CavliRunningStatusDatabase()


def change_operator(operator_code):
    
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        #print("Serial connection established.")
        pass
    else:
        print("Serial connection failed.")
        return False

    tryConnCommand = [
        ('AT+COPS=1,2,"{}",7'.format(operator_code), 'OK', 2),
        #('AT+COPS=0', 'OK', 5),
        ('AT+TRB', 'RDY', 30)
    ]

    # Execute commands sequentially
    for command, expected_response, delay in tryConnCommand:
        if not serial_commander.send_command(command, expected_response, delay):
            print("Error occurred while executing command:", command)
            return False

    serial_commander.clear_serial_port()
    serial_commander.close_serial()

    initialize_gnss()
    
    return True


def initialize_device():
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        #print("Serial connection established.")
        pass
    else:
        print("Serial connection failed.")
        return False

    commands = [
        ('AT', 'OK', 1),
        ('ATQ0', 'OK', 1),
        ('AT+COPS?', 'OK', 5),
        ('AT+CEREG?', 'OK', 2),
        ('AT+CGACT?', 'OK', 1)
    ]

    # Execute commands sequentially
    for command, expected_response, delay in commands:
        if not serial_commander.send_command(command, expected_response, delay):
            print("Error occurred while executing command:", command)
            return False

    serial_commander.clear_serial_port()
    serial_commander.close_serial()
    return True


def initialize_gnss():
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        print("Serial connection established.")
        #pass
    else:
        print("Serial connection failed.")
        #pass
        #return False

    commands = [
        ('AT+CGPS=1', 'OK', 2)
    ]

    # Execute commands sequentially
    for command, expected_response, delay in commands:
        if not serial_commander.send_command(command, expected_response, delay):
            print("Error occurred while executing command:", command)
            #return False

    serial_commander.clear_serial_port()
    serial_commander.close_serial()
    #return True


def operator_info():
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        #print("Serial connection established.")
        pass
    else:
        print("Serial connection failed.")
        return False

    commands = [
        ('AT+COPS?', 'OK', 10),
    ]

    # Execute commands sequentially
    #for command, expected_response, delay in commands:
    #    if not serial_commander.send_command(command, expected_response, delay):
    #        print("Error occurred while executing command:", command)
    #        return False
    for command, expected_response, delay in commands:
        success, response = serial_commander.send_command_and_get_response(command, expected_response, delay)

    getOperatorInfo(response)

    serial_commander.clear_serial_port()
    serial_commander.close_serial()
    return True

#success, response 

def check_network_ip():
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        #print("Serial connection established.")
        pass
    else:
        print("Serial connection failed.")
        return False

    chkNetIPCommand = [
        ('AT+CDNSGIP="mqtt.thingsboard.cloud"', 'OK', 5)
    ]

    # Execute commands sequentially
    for command, expected_response, delay in chkNetIPCommand:
        if not serial_commander.send_command(command, expected_response, delay):
            print("Error occurred while executing command:", command)
            return False

    serial_commander.clear_serial_port()
    serial_commander.close_serial()
    return True

def get_IMEI_number():
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        #print("Serial connection established.")
        pass
    else:
        print("Serial connection failed.")
        return False

    commands = [
        ('ATI', 'OK', 10),
    ]

    #for command, expected_response, delay in commands:
    #    success, response = serial_commander.send_command_and_get_response_non_ascii_format(command, expected_response, delay)

    # Send the ATI command and print the response
    response = serial_commander.send_command_and_print_response('ATI')
    #print(response)

    # Extract the second element from the tuple (the string)
    response_string = response[1]

    # Split the response into lines
    lines = response_string.split('\r\n')

    # Initialize a dictionary to store the parsed values
    parsed_values = {}

    # Loop through each line and split into key-value pairs
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            parsed_values[key] = value
        elif line.strip() != "":  # Ignore empty lines
            parsed_values['Status'] = line.strip()

    # Accessing specific information and assigning to variables
    manufacturer = parsed_values.get("Manufacturer")
    model_name = parsed_values.get("Model Name")
    description = parsed_values.get("Description")
    firmware_release = parsed_values.get("Firmware Release")
    imei = parsed_values.get("IMEI")
    serial_number = parsed_values.get("Serial Number")
    hw_version = parsed_values.get("HW Version")
    part_number = parsed_values.get("Part Number")
    build_date = parsed_values.get("Build Date")

    # Optionally, print the variables for verification
#    print 'Manufacturer:', manufacturer
#    print 'Model Name:', model_name
#    print 'Description:', description
#    print 'Firmware Release:', firmware_release
    print 'IMEI:', imei
    print 'Serial Number:', serial_number
#    print 'HW Version:', hw_version
#    print 'Part Number:', part_number
#    print 'Build Date:', build_date

    # Close the serial connection
    #serial_commander.close_serial()

    cavli_database.update_cavli_running_parameters('IMEI', imei)
    cavli_database.update_cavli_running_parameters('SerialNumber', serial_number)
    
    serial_commander.clear_serial_port()
    serial_commander.close_serial()
    return True


def try_connection():
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        #print("Serial connection established.")
        pass
    else:
        print("Serial connection failed.")
        return False

    tryConnCommand = [
        ('AT+CFUN=0', 'OK', 1),
        ('AT+CFUN=1', 'OK', 1),
        ('AT+CIMI', 'OK', 1)
    ]

    # Execute commands sequentially
    for command, expected_response, delay in tryConnCommand:
        if not serial_commander.send_command(command, expected_response, delay):
            print("Error occurred while executing command:", command)
            return False

    serial_commander.clear_serial_port()
    serial_commander.close_serial()
    return True

def reset_device():
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        #print("Serial connection established.")
        pass
    else:
        print("Serial connection failed.")
        return False


    rstCommands = [
        ('AT+TRB', 'OK', 30)
    ]

    # Execute commands sequentially
    for command, expected_response, delay in rstCommands:
        #if not serial_commander.send_command(command, expected_response, delay):
        if not serial_commander.send_command_and_get_response(command, expected_response, delay):
            print("Error occurred while executing command:", command)
            time.sleep(10)
            return False

    serial_commander.clear_serial_port()
    serial_commander.close_serial()
    
    time.sleep(15)

    initialize_gnss()

    return True


def connect_to_server():

    clientId = str(modem_config_db.get_parameter('client_id'))
    userName = str(modem_config_db.get_parameter('user_name'))
    password = str(modem_config_db.get_parameter('password'))
    
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        #print("Serial connection established.")
        pass
    else:
        print("Serial connection failed.")
        return False

    connServerCommand = [
        ('AT+MQTTCREATE="mqtt.thingsboard.cloud",1883,"{}",90,0,"{}","{}"'.format(clientId, userName, password), 'OK', 15),
        ('AT+MQTTCONN=3', 'OK', 30),
        ('AT+MQTTSUBUNSUB=3,"v1/devices/me/telemetry",1,1', 'OK', 10)
    ]

    # Execute commands sequentially
    for command, expected_response, delay in connServerCommand:
        if not serial_commander.send_command(command, expected_response, delay):
            print("Error occurred while executing command:", command)
            return False

    serial_commander.clear_serial_port()
    serial_commander.close_serial()
    return True


def connect_to_server_old():
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        #print("Serial connection established.")
        pass
    else:
        print("Serial connection failed.")
        return False

    #Dexter6.1 : {clientId:"jgtgnopl9ba4fwsvthij",userName:"i9mr50dbhkfu58jgebbm",password:"47oip8zdftslhokdyl61"}
    #Dexter6.2 : {clientId:"aydo1t1mweyoe3zs939m",userName:"vtyf59jmg8gmi7xi7vqx",password:"v5v2x0vkffly0gtsz3vt"}
    #Dexter6.3 : {clientId:"a60alowglf2wr7r3beuj",userName:"s4i1x2geszkz6oj7q8f2",password:"8hqpdy6qlhtgtptno2e6"}
    #Dexter6.4 : {clientId:"tzth27bnb75she6je3qc",userName:"so3ohvpnoki52ti1k39k",password:"0ky6hfeny57rn7pcbhrv"}
    #Dexter6.5 : {clientId:"u8vv15xntm7ej2ykym2u",userName:"417d8yts3p3zxi8888r7",password:"lcpvry6rzqo1m60l3z1b"}
    
    connServerCommand = [
        ('AT+MQTTCREATE="mqtt.thingsboard.cloud",1883,"jgtgnopl9ba4fwsvthij",90,0,"i9mr50dbhkfu58jgebbm","47oip8zdftslhokdyl61"', 'OK', 15), # 6.1
        #('AT+MQTTCREATE="mqtt.thingsboard.cloud",1883,"aydo1t1mweyoe3zs939m",90,0,"vtyf59jmg8gmi7xi7vqx","v5v2x0vkffly0gtsz3vt"', 'OK', 15),  # 6.2                              
        #('AT+MQTTCREATE="mqtt.thingsboard.cloud",1883,"a60alowglf2wr7r3beuj",90,0,"s4i1x2geszkz6oj7q8f2","8hqpdy6qlhtgtptno2e6"', 'OK', 15), # 6.3
        #('AT+MQTTCREATE="mqtt.thingsboard.cloud",1883,"tzth27bnb75she6je3qc",90,0,"so3ohvpnoki52ti1k39k","0ky6hfeny57rn7pcbhrv"', 'OK', 15), # 6.4
        #('AT+MQTTCREATE="mqtt.thingsboard.cloud",1883,"u8vv15xntm7ej2ykym2u",90,0,"417d8yts3p3zxi8888r7","lcpvry6rzqo1m60l3z1b"', 'OK', 15), # 6.5
        ('AT+MQTTCONN=3', 'OK', 30),
        ('AT+MQTTSUBUNSUB=3,"v1/devices/me/telemetry",1,1', 'OK', 10)
    ]

    # Execute commands sequentially
    for command, expected_response, delay in connServerCommand:
        if not serial_commander.send_command(command, expected_response, delay):
            print("Error occurred while executing command:", command)
            return False


    serial_commander.clear_serial_port()
    serial_commander.close_serial()
    return True

def check_mqtt_status():
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        #print("Serial connection established.")
        pass
    else:
        print("Serial connection failed.")
        return False

    chkMQTTStatusCommand = [
        ('AT+MQTTSTATUS=3', '+MQTTSTATUS: 1', 2)
    ]

    # Execute commands sequentially
    for command, expected_response, delay in chkMQTTStatusCommand:
        if not serial_commander.send_command(command, expected_response, delay):
            print("Error occurred while executing command:", command)
            return False

    serial_commander.clear_serial_port()
    serial_commander.close_serial()
    return True


def switch_sim(sim_type):
    if sim_type not in ['physical', 'esim']:
        print("Invalid SIM type.")
        return False

    serial_commander = SerialCommander()
    try:
        serial_commander.initialize_serial()
    except Exception as e:
        print("Initialization failed: {}".format(e))
        return False

    if not serial_commander.test_serial_connection():
        print("Serial connection failed.")
        return False

    sim_command = 'AT^SIMSWAP=1' if sim_type == 'physical' else 'AT^SIMSWAP=0'

    commands = [
        (sim_command, 'OK', 30),
        ('AT+TRB', 'OK', 120),
        ('AT^SIMSWAP?', 'OK', 30)
    ]

    max_retries = 3
    for i, (command, expected_response, delay) in enumerate(commands):
        success = False
        for attempt in range(max_retries):
            if serial_commander.send_command(command, expected_response, delay):
                success = True
                break
            else:
                print("Attempt {} for command {} failed.".format(attempt + 1, command))
                time.sleep(1)  # Adding a small delay between retries
        if not success:
            print("Command {} failed after {} attempts.".format(command, max_retries))
            serial_commander.clear_serial_port()
            serial_commander.close_serial()
            return False
        # Wait for 30 seconds after the 'AT+TRB' command before sending the next command
        if command == 'AT+TRB':
            print("Waiting for 30 seconds before sending the next command.")
            time.sleep(30)

    serial_commander.clear_serial_port()
    serial_commander.close_serial()

    initialize_gnss()
    
    return True



#def get_lat_long_old():
#    serial_commander = SerialCommander()
#    serial_commander.initialize_serial()

#    if serial_commander.test_serial_connection():
#        print("Serial connection established.")
        #pass
#    else:
#        print("Serial connection failed.")
        #return False

#    tryConnCommand = [
        #('AT+CGPS=1', 'OK', 1),
#        ('AT+CGPSGPOS=5', 'OK', 1)
#    ]

    # Execute commands sequentially
#    for command, expected_response, delay in tryConnCommand:
#        if not serial_commander.send_command(command, expected_response, delay):
#            print("Error occurred while executing command:", command)
            #return False

#    serial_commander.clear_serial_port()
#    serial_commander.close_serial()
    #return True


def get_lat_long():
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if serial_commander.test_serial_connection():
        print("Serial connection established.")
        #pass
    else:
        print("Serial connection failed.")
        #return False

    tryConnCommand = [
        #('AT+CGPS=1', 'OK', 1),
        ('AT+CGPSGPOS=5', 'OK', 1)
    ]

    # Execute commands sequentially
    error_occurred = False
    for command, expected_response, delay in tryConnCommand:
        success, response = serial_commander.send_command_and_get_response(command, expected_response, delay)
        if not success:
            print("Error occurred while executing command:", command)
            error_occurred = True
            #return False
        else:
#            print("Response:", response)
            print("Command executed successfully:", command)

            latitude, longitude = parse_lat_long(response)
            if latitude is not None and longitude is not None:
                print("Latitude:", latitude)
                print("Longitude:", longitude)
                cavli_database.update_cavli_running_parameters('latitude', latitude)
                cavli_database.update_cavli_running_parameters('longitude', longitude)
            else:
                print("Failed to parse latitude and longitude.")
            

    if not error_occurred:
        print("All commands executed successfully.")
        #return True

    serial_commander.clear_serial_port()
    serial_commander.close_serial()




# Example usage:
# To switch to physical SIM:
# switch_sim(serial_commander, 'physical')

# To switch to eSIM:
# switch_sim(serial_commander, 'esim')


#def send_payload_v1(payload):
#    serial_commander = SerialCommander()
#    serial_commander.initialize_serial()

#    print(" *** Pyload Testing *** ")
#    print(payload)

#    if serial_commander.test_serial_connection():
        #print("Serial connection established.")
#        pass
#    else:
#        print("Serial connection failed.")
#        return False

#    sendPayloadCommand = [    
#        ('AT+MQTTPUBLM=3,v1/devices/me/telemetry,1,0,0', '>', 2),
#        (payload, None, 2),
#        ('\x1A', 'OK', 10)
#    ]

    # Execute commands sequentially
#    for command, expected_response, delay in sendPayloadCommand:
        #if not serial_commander.send_command(command, expected_response, delay):
#        if not serial_commander.send_command_and_get_response(command, expected_response, delay):
#            print("Error occurred while executing command:", command)
#            return False

#    serial_commander.clear_serial_port()
#    serial_commander.close_serial()
#    return True


def send_payload(payload):
    serial_commander = SerialCommander()
    serial_commander.initialize_serial()

    if not serial_commander.test_serial_connection():
        print("Serial connection failed.")
        return False

    print(" ********** Pyload Testing ********* ")
    print(payload)

    # Check the payload using json_db_module
    is_match = json_db_module.check_incoming_json(payload)
    print(" ********** Is Match ********* ")
    print(is_match)
    print(" ********** Is Match ********* ")
    
    # Determine the appropriate AT command based on the payload check
    if is_match:
        # If match, use telemetry topic
        sendPayloadCommand = [    
            ('AT+MQTTPUBLM=3,v1/devices/me/attributes,1,0,0', '>', 2),
            (payload, None, 2),
            ('\x1A', 'OK', 10)
        ]
    else:
        # Otherwise, use attributes topic

        sendPayloadCommand = [    
            ('AT+MQTTPUBLM=3,v1/devices/me/telemetry,1,0,0', '>', 2),
            (payload, None, 2),
            ('\x1A', 'OK', 10)
        ]        

    # Execute commands sequentially
    for command, expected_response, delay in sendPayloadCommand:
        if not serial_commander.send_command_and_get_response(command, expected_response, delay):
            print("Error occurred while executing command:", command)
            return False

    serial_commander.clear_serial_port()
    serial_commander.close_serial()
    return True




def lookup_operator(code):

    lookup_date = {
        4051: "Reliance",
        40401: "Vi",
        40402: "AirTel",
        40503: "Reliance",
        40403: "AirTel",
        40504: "Reliance",
        40404: "Vi",
        40505: "Reliance",
        40405: "Vi",
        40506: "Reliance",
        40507: "Reliance",
        40407: "Vi",
        40508: "Reliance",
        40509: "Reliance",
        40409: "Reliance",
        40510: "Reliance",
        40410: "AirTel",
        40511: "Reliance",
        40411: "Vi",
        40512: "Reliance",
        40412: "Vi",
        40513: "Reliance",
        40413: "Vi",
        40514: "Reliance",
        40414: "Vi",
        40515: "Reliance",
        40415: "Vi",
        40416: "AirTel",
        40517: "Reliance",
        40417: "AIRCEL",
        40518: "Reliance",
        40418: "Reliance",
        40519: "Reliance",
        40419: "Vi",
        40520: "Reliance",
        40420: "Vi",
        40521: "Reliance",
        40421: "LoopMobile",
        40522: "Reliance",
        40422: "Vi",
        40523: "Reliance",
        40424: "Vi",
        40525: "Airtel",
        40425: "AIRCEL",
        40526: "Airtel",
        40527: "Airtel",
        40427: "Vi",
        40528: "Airtel",
        40428: "AIRCEL",
        40529: "Airtel",
        40429: "AIRCEL",
        40530: "Airtel",
        40430: "Vi",
        40531: "Airtel",
        40431: "AirTel",
        40532: "Airtel",
        40533: "Airtel",
        40534: "Airtel",
        40434: "BSNL",
        40535: "Airtel",
        40435: "AIRCEL",
        40536: "Airtel",
        40436: "Reliance",
        40537: "Airtel",
        40437: "AIRCEL",
        40538: "Airtel",
        40438: "BSNL",
        40539: "Airtel",
        40440: "AirTel",
        40541: "Airtel",
        40441: "AIRCEL",
        40542: "Airtel",
        40442: "AIRCEL",
        40543: "Airtel",
        40443: "Vi",
        40544: "Airtel",
        40444: "Vi",
        40545: "Airtel",
        40445: "Airtel",
        40546: "Airtel",
        40446: "Vi",
        40547: "Airtel",
        40448: "DishnetWireless",
        40449: "Airtel",
        40450: "Reliance",
        40551: "AirTel",
        40451: "BSNL",
        40552: "AirTel",
        40452: "Reliance",
        40553: "AirTel",
        40453: "BSNL",
        40554: "AirTel",
        40454: "BSNL",
        40555: "Airtel",
        40455: "BSNL",
        40556: "AirTel",
        40456: "Vi",
        40457: "BSNL",
        40458: "BSNL",
        40459: "BSNL",
        40460: "Vi",
        40462: "BSNL",
        40464: "BSNL",
        40566: "Vi",
        40466: "BSNL",
        40567: "Vi",
        40467: "Reliance",
        40468: "DOLPHIN",
        40469: "DOLPHIN",
        40570: "Vi",
        40470: "AirTel",
        40471: "BSNL",
        40472: "BSNL",
        40473: "BSNL",
        40474: "BSNL",
        40475: "BSNL",
        40476: "BSNL",
        40477: "BSNL",
        40478: "Vi",
        40479: "BSNL",
        40480: "BSNL",
        40481: "BSNL",
        40482: "Vi",
        40483: "Reliance",
        40484: "Vi",
        40485: "Reliance",
        40486: "Vi",
        40487: "Vi",
        40488: "Vi",
        40489: "Vi",
        40490: "AirTel",
        40491: "AIRCEL",
        40492: "AirTel",
        40493: "AirTel",
        40494: "AirTel",
        40495: "AirTel",
        40496: "AirTel",
        40497: "AirTel",
        40498: "AirTel",
        405750: "Vi",
        405751: "Vi",
        405752: "Vi",
        405753: "Vi",
        405754: "Vi",
        405755: "Vi",
        405756: "Vi",
        405799: "Vi",
        405800: "AIRCEL",
        405801: "AIRCEL",
        405803: "AIRCEL",
        405804: "AIRCEL",
        405805: "AIRCEL",
        405806: "AIRCEL",
        405809: "AIRCEL",
        405810: "AIRCEL",
        405811: "AIRCEL",
        405818: "Uninor",
        405819: "Uninor",
        405820: "Uninor",
        405821: "Uninor",
        405822: "Uninor",
        405827: "VideoconDatacom",
        405840: "Jio",
        405845: "Vi",
        405846: "Vi",
        405847: "Vi",
        405848: "Vi",
        405849: "Vi",
        405850: "Vi",
        405851: "Vi",
        405852: "Vi",
        405853: "Vi",
        405854: "Jio",
        405855: "Jio",
        405856: "Jio",
        405857: "Jio",
        405858: "Jio",
        405859: "Jio",
        405860: "Jio",
        405861: "Jio",
        405862: "Jio",
        405863: "Jio",
        405864:	"Jio",
        405865:	"Jio",
        405866:	"Jio",
        405867:	"Jio",
        405868:	"Jio",
        405869:	"Jio",
        405870:	"Jio",
        405871:	"Jio",
        405872:	"Jio",
        405873:	"Jio",
        405874:	"Jio",
        405880:	"Uninor",
        405908:	"Vi",
        405909:	"Vi",
        405910:	"Vi",
        405911:	"Vi",
        405927:	"Uninor",
        405929:	"Uninor"
    }

    if int(code) in lookup_date:
        return lookup_date[int(code)]
    else:
        return "Operator not found for the given code."


#def parse_lat_long_old(gnrmc_string):
#    try:
#        parts = gnrmc_string.split(',')
#        if len(parts) >= 6:
#            latitude = float(parts[3][:2]) + float(parts[3][2:]) / 60
#            if parts[4] == 'S':
#                latitude = -latitude
#            longitude = float(parts[5][:3]) + float(parts[5][3:]) / 60
#            if parts[6] == 'W':
#                longitude = -longitude
#            return latitude, longitude
#        else:
#            return None, None
#    except Exception as e:
#        print("An error occurred while parsing the string:", e)
#        return None, None

def parse_lat_long(gnrmc_string):
    try:
        parts = gnrmc_string.split(',')
        if len(parts) >= 6:
            # Parse latitude
            lat_deg = float(parts[3][:2])
            lat_min = float(parts[3][2:])
            latitude = lat_deg + lat_min / 60
            if parts[4] == 'S':
                latitude = -latitude

            # Parse longitude
            lon_deg = float(parts[5][:3])
            lon_min = float(parts[5][3:])
            longitude = lon_deg + lon_min / 60
            if parts[6] == 'W':
                longitude = -longitude

            # Format to four decimal places
            latitude = round(latitude, 4)
            longitude = round(longitude, 4)

            return latitude, longitude
        else:
            return None, None
    except Exception as e:
        print("An error occurred while parsing the string:", e)
        return None, None


def getOperatorInfo(response):
    global attempts
    network_type = 0
    operator_id = 0
    network_status = 0

    # Split the response by newline characters
    split_response = response.split('\r\n')

    # Extract the relevant part of the response
    data_response = split_response[0]

    # Split the data part of the response by comma
    split_data = data_response.split(',')

    # Extract relevant information
    mode = split_data[0].split(':')[1].strip()
    try:
        network_type = split_data[1]
        operator_id = split_data[2].strip('"')
        network_status = split_data[3]
        
        cavli_database.update_cavli_running_parameters('serviceProvider', lookup_operator(int(operator_id)))
        
    except IndexError:
        # Handling missing parts in the split_data
        pass

    except UnboundLocalError as e:
        # Handle unbound local error
        pass

    except ValueError as e:
        # Handle value error
        pass

    except Exception as e:
        # Handle any other unforeseen exceptions
        pass

    print("No of Attempts for Sim Switch:", str(attempts))

    if cavli_database.get_sim_swap() == 'esim':
        try:
            if lookup_operator(int(operator_id)) != 'Jio':
                attempts += 1
                main(None, str(5))

                if attempts >= 5:
                    attempts = 0
                    print("Number of attempts exceeded. Switching to Physical SIM.")
                    switch_to_physical_sim()
                else:
                    print("Failed to switch to Jio. Attempting again...")
            else:
                attempts = 0

        except UnboundLocalError:
            pass

        except IndexError:
            print(lookup_operator(int(0)))
            pass
    else:
        attempts = 0

#import re
#def getIMEIInfo(response):
    # Define regex patterns for each field
#    patterns = {
#        'Manufacturer': r'Manufacturer:\s*(.*)',
#        'Model Name': r'Model Name:\s*(.*)',
#        'Description': r'Description:\s*(.*)',
#        'Firmware Release': r'Firmware Release:\s*(.*)',
#        'IMEI': r'IMEI:\s*(.*)',
#        'Serial Number': r'Serial Number:\s*(.*)',
#        'HW Version': r'HW Version:\s*(.*)',
#        'Part Number': r'Part Number:\s*(.*)',
#        'Build Date': r'Build Date:\s*(.*)'
#    }
    
    # Extract the information
#    info = {}
#    for key, pattern in patterns.items():
#        match = re.search(pattern, response, re.MULTILINE)
#        if match:
#            info[key] = match.group(1)
    
#    return info

# Extract and save the information into a variable
#device_info = parse_ati_response(response)

# Retrieve and print the IMEI number
#imei_number = device_info.get('IMEI')
#print(f"IMEI: {imei_number}")


def switch_to_physical_sim():
    print("Switching to Physical SIM...")
    main('physical', str(3))
    # Logic to switch to Physical SIM goes here
    # This can include hardware-specific commands or API calls

def switch_to_esim_sim():
    print("Switching to e SIM...")
    main('esim', str(3))
    main(None, str(5))
    time.sleep(10)
    main(None, str(5))
    # Logic to switch to Physical SIM goes here
    # This can include hardware-specific commands or API calls


def initCalviDevice():
    
    success = initialize_device()
    if success:
        print("Device initialized successfully.")
        operator_info()
        #get_lat_long()
        get_IMEI_number()
#        executor.increment()
    else:
        print("Error occurred during initialization.")
        return False


def initOperatorIMEI():
    
    success = operator_info()
    if success:
#        print("Get Network Provider Successfully.")
        #get_lat_long()
        get_IMEI_number()
#        executor.increment()
    else:
        print("Error occurred during initialization.")
        return False


#def checkOperator():

#    success_ip = check_network_ip()
#    if success_ip:
#        print("Network IP checked successfully.")
#    else:
#        print("Error occurred while checking network IP.")

#    if not success_ip:
#        success_try_conn = try_connection()
#        if success_try_conn:
#            print("Connection attempt successful.")
#        else:
#            print("Error occurred while attempting connection.")

#        if not success_try_conn:
#            success_reset = reset_device()
#            if success_reset:
#                print("Device reset successful.")
#            else:
#                print("Error occurred while resetting the device.")


def checkMQTTStatus(paylod):

   
    success_mqtt_status = check_mqtt_status()

    if success_mqtt_status:
        print("MQTT status checked successfully.")

        #success_send_payload = send_payload(paylod_ref())
        success_send_payload = send_payload(paylod)
       
        if success_send_payload:
            print("Payload sent successfully.")
            return True
        else:
            print("Error occurred while sending payload.")
        
    else:
        print("Error occurred while checking MQTT status.")

        success_conn_server = connect_to_server()
    
        if success_conn_server:
            print("Connected to server successfully.")


            success_mqtt_status = check_mqtt_status()

            if success_mqtt_status:
                print("MQTT status checked successfully.")


                #success_send_payload = send_payload(paylod_ref())
                success_send_payload = send_payload(paylod)
                
                if success_send_payload:
                    cavli_database.update_cavli_running_parameters('dataSending', "Success")
                    print("Payload sent successfully.")
                    return True
                else:
                    print("Error occurred while sending payload.")
                    return False

            else:
                print("Error occurred while checking MQTT status.")
                return False
        
        else:
            print("Error occurred while connecting to server.")
            return 2

        #return True:

#def sendData():
    
    
#    success_mqtt_status = check_mqtt_status()

#    if success_mqtt_status:
#        print("MQTT status checked successfully.")

#        success_send_payload = send_payload(paylod_ref())
        
#        if success_send_payload:
#            print("Payload sent successfully.")
#        else:
#            print("Error occurred while sending payload.")
        
#    else:
#        print("Error occurred while checking MQTT status.")

#        success_conn_server = connect_to_server()
    
#        if success_conn_server:
#            print("Connected to server successfully.")

#            success_send_payload = send_payload(paylod_ref())
        
#            if success_send_payload:
#                print("Payload sent successfully.")
#            else:
#                print("Error occurred while sending payload.")
        
#        else:
#            print("Error occurred while connecting to server.")


def paylod_ref(): #used for testing data sending
    
    branch_t = "mumbai"
    branch = str("\"") + str(branch_t) + str("\"")
        
    payload="{"
    payload+="\"branch\":";
    payload+=str(branch)
    payload+="}"

    return payload


def create_incrementer(max_value):
    def increment():
        increment.counter += 1
        if increment.counter > max_value:
            increment.counter = 0
        return increment.counter
    increment.counter = 0
    return increment


class ChildProgram:
    def __init__(self, db_handler):
        self.db_handler = db_handler

    def send_to_cloud(self, data):
        print("Sending to cloud:", data)
        time.sleep(2)
        print("Data sent to the cloud successfully.")
        return data

    def run(self):
        while True:
            row_id, json_str = self.db_handler.get_json_string()
            if json_str:
                self.send_to_cloud(json_str)
                self.db_handler.mark_as_sent(row_id)
            else:
                print("No new data to send. Checking again in 5 seconds.")
                time.sleep(5)


#def reset_payload(db_handler, row_id):
#    """Manually reset the status of a specific payload to pending."""
#    db_handler.reset_status(row_id)
#    print("Payload with row_id {} has been reset to pending.".format(row_id))


#def execute_logic(flag):
#    if flag:
#        row_id, json_str = db_handler.get_json_string()
#        if json_str:
#            child_program.send_to_cloud(json_str)
#            db_handler.mark_as_failed(row_id)  # Mark as Failed always
#        else:
#            print("No new data to send. Checking again in 5 seconds.")
#            time.sleep(5)
#        result = "True logic executed"
#    else:
#        print("No new data to send. Checking again in 5 seconds.")
#        time.sleep(5)
#        result = "False logic executed"
    
#    return result



class CounterExecutor:
    def __init__(self, n, function):
        self.n = n
        self.function = function
        self.count = 0

    def increment(self):
        self.count += 1
        if self.count >= self.n:
            self.function()
            self.count = 0  # Reset the counter if you want to reuse it

# Example function to be executed
#def my_function():
#    print("Function executed!")

# Number of counts after which the function should be executed
n = 5

# Create an instance of CounterExecutor
#executor = CounterExecutor(n, my_function)
executor = CounterExecutor(n, get_lat_long)


def main(param1, param2):
    
    # Initialize a variable
    count = 0

    # Perform some actions
    #print("Count is:", count)
    
    # Increment the count
    #count += 1

    #param2 = 1
    #param1 = '405873'
    #param1 = '40430'
    #param1 = '40482'

    # Define an incrementer with a maximum value of 5
    incrementer = create_incrementer(2)

    # Start the do-while loop

    #cavli_database.update_cavli_running_parameters('dataSending', "Error")
    
    cavli_database.update_cavli_running_parameters('modemStatus', "Running")
    cavli_database.update_cavli_running_parameters('dataSending', "Executing")

    while True:
        if param2 == '0':
            break
        elif param2 == '1':
            #param1 = paylod_ref()
            success = checkMQTTStatus(param1)
            if success == True:
                print(success)
                cavli_database.update_cavli_running_parameters('dataSending', "Success")
                cavli_database.update_cavli_running_parameters('modemStatus', "Ready")
                break
            elif success == False:
                print(success)
                if initCalviDevice() == False:
                    break
            elif success == 2:
                #try_connection()
                reset_device()
                if check_network_ip() == False:
                    #try_connection()
                    reset_device()
                if check_network_ip() == False:
                    reset_device()
                    if incrementer() == 2:
                        cavli_database.update_cavli_running_parameters('dataSending', "Error")
                        cavli_database.update_cavli_running_parameters('modemStatus', "Ready")
                        break
                    #    switch_sim('physical')
                    #    reset_device()
                    #    cavli_database.update_cavli_running_parameters('simSwap', 'physical')
                
        elif param2 == '2':
            initCalviDevice()
            cavli_database.update_cavli_running_parameters('modemStatus', "Ready")
            break
        
        elif param2 == '3':
            switch_sim(param1) # 'physical' / 'esim'
            #switch_sim('esim') # 'physical' / 'esim'
            time.sleep(10)
            #reset_device()
            cavli_database.update_cavli_running_parameters('simSwap', param1)
            cavli_database.update_cavli_running_parameters('modemStatus', "Ready")
            time.sleep(30)
            break
           
        elif param2 == '4':
            reset_device()
            cavli_database.update_cavli_running_parameters('modemStatus', "Ready")
            break

        elif param2 == '5':
            #change_operator(param1)
            change_operator(str(405873))
            cavli_database.update_cavli_running_parameters('modemStatus', "Ready")
            time.sleep(30)
            break

        elif param2 == '6':
            initOperatorIMEI()
            cavli_database.update_cavli_running_parameters('modemStatus', "Ready")
            break
        
        elif param2 == '7':
            break


if __name__ == "__main__":

    print "Cavli Serial Program"
    
    db_handler = DatabaseHandler()
    child_program = ChildProgram(db_handler)
    modem_config_db = ModemConfigDatabase()
    
    cavli_database.update_cavli_running_parameters('latitude', 20.5937)
    cavli_database.update_cavli_running_parameters('longitude', 78.9629)
    cavli_database.update_cavli_running_parameters('serviceProvider', "NA")
    cavli_database.update_cavli_running_parameters('IMEI', 0)
    cavli_database.update_cavli_running_parameters('SerialNumber', 0)
    
    print "Setting up modem..."

#    time.sleep(60)

#    reset_device()

    time.sleep(30)
    
    main(None, str(2))
    switch_to_esim_sim()
    #switch_to_physical_sim()
    
    time.sleep(30)
    
    # Create a new context with an initial state and parameters.
    context = Context(InitializeModem, modem_id=1234, network="5G")

#    print("Initial State:", context)

   
    while True:

        # Simulate the `initialize` event to transition to `CheckNetworkStatus`
        context.on_event('initialize')
#        print "Current State after initialize:", context
       
        watchdog.reset()  # Reset watchdog after 5min
        
        # Simulate the `network_check` event to transition to `CheckNetworkStatus`
        context.on_event('network_check')
#        print "Current State after network_check:", context

        # Simulate the `signal_strength` event to transition to `CheckSignalStrength`
        context.on_event('signal_strength')
#        print "Current State after signal_strength:", context

        context.on_event('send_payload')
#        print "Current State after send_payload:", context

        context.on_event('confirm_delivery')
#        print "Current State after confirm_delivery:", context

        time.sleep(10)



#        for event in events:
#            # Handle the event and transition to the next state
#            context.on_event(event)
#            # Print the current state
#            print("Current State:", context)

    
        
#if __name__ == "__main__":
#    # Create a new context with an initial state and parameters.
#    context = Context(InitializeModem, modem_id=1234, network="5G")
#
#    print("Initial State:", context)
#
#    # List of events to simulate program logic
#    events = ['network_check', 'signal_strength', 'send_payload', 'confirm_delivery', 'terminate', 'initialize', 'network_check']
#
#    for event in events:
#        # Handle the event and transition to the next state
#        context.on_event(event)
#        # Print the current state
#        print("Current State:", context)

                
