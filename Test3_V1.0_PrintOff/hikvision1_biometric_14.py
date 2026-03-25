# -*- coding: utf-8 -*-
# !/usr/local/bin/python


import requests
from requests.auth import HTTPDigestAuth
import warnings
import json
import paho.mqtt.client as paho  		    #mqtt library
import time

from hikvisionapi import Client
import xml.etree.ElementTree as ET
import re
import time

import threading
import os
import sys

from buffer_manager import insert_json_to_db
import device_parameters_module  # Assuming the second script is named 'device_parameters_module.py'



import logical_params_module
# Initialize the database
logical_params_module.initialize_database()


class SoftwareWatchdog:
    def __init__(self, timeout=1800):
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

    #def _restart_program(self):
     #   """ Restart the script using OS system call. """
      #  python = sys.executable
       # os.execl(python, python, *sys.argv)  # Restart the same script
  
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
                    "Module Reboot": "Hik BACS",
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
  
# Initialize software watchdog with 1800-second timeout
watchdog = SoftwareWatchdog(timeout=1800)



#device_type = 'HikvisionBioMetric1'
#devices = device_parameters_module.get_device_parameters(device_type)

#print(devices)

#ipaddress_d = devices[0][2]
#username_d = devices[0][3]
#password_d = devices[0][4]

# Replace with the actual IP address or domain of your Dahua NVR/DVR
#server_ip = '192.168.0.115'
#print(ipaddress_d)
#server_ip = ipaddress_d

# Credentials for authentication
#username = 'admin'
#password = 'sepl1234'

#print(username_d)
#print(password_d)

#username = username_d
#password = password_d

#import device_parameters_module  # Assuming this module provides device configurations.

def get_device_credentials(device_type):
    """
    Retrieve the server IP, username, and password for a given device type.

    :param device_type: The type of the device (e.g., 'HikvisionBioMetric1').
    :return: A tuple containing (server_ip, username, password).
    """
    try:
        # Fetch device parameters from the module.
        devices = device_parameters_module.get_device_parameters(device_type)

        # Assuming the returned structure: a list of tuples where each tuple contains:
        # (id, name, ip_address, username, password, ...)
        if not devices or len(devices[0]) < 5:
            raise ValueError("Device parameters are missing or invalid format.")

        # Extracting the relevant parameters.
        server_ip = devices[0][2]
        username = devices[0][3]
        password = devices[0][4]

        # Return the extracted credentials.
        return server_ip, username, password

    except Exception as e:
        print("Error retrieving device credentials: {}".format(str(e)))
        return None, None, None



#e7fvTSRgsbgQtUZu2SC5#
ACCESS_TOKEN='e7fvTSRgsbgQtUZu2SC5'
broker='www.dexterhms.com'
port=1883 					    #data listening port

#def on_publish(client,userdata,result):             #create function for callback
#    print("data published to thingsboard \n")
#    pass

#client1= paho.Client("control1")                    #create client object
#client1.on_publish = on_publish                     #assign function to callback
#client1.username_pw_set(ACCESS_TOKEN)               #access token from thingsboard device
#client1.connect(broker,port,keepalive=60)           #establish connection

# Suppress the SSL warning
warnings.filterwarnings("ignore", message="Unverified HTTPS request")



# Request Params (key=value format in URL)


#request_url = 'http://192.168.0.115:80/ISAPI/System/deviceInfo'
# Set the authentication information
#auth = requests.auth.HTTPDigestAuth('admin', 'sepl1234')
# Send the request and receive response
#response = requests.get(request_url, auth=auth)
# Output response content
#url = 'http://{}/ISAPI/System/deviceInfo'.format(server_ip)
# Returns XML

#10.2.3.5 Get the working status of the Access Control
#GET /ISAPI/AccessControl/AcsWorkStatus?format=json
#request_url = 'http://192.168.0.115:80/ISAPI/AccessControl/AcsWorkStatus'
# Set the authentication information
#auth = requests.auth.HTTPDigestAuth('admin', 'sepl1234')
# Send the request and receive response
#response = requests.get(request_url, auth=auth)
# Output response content
#url = 'http://{}/ISAPI/AccessControl/AcsWorkStatus'.format(server_ip)
# Returns JSON

#10.2.7.20 Get the parameters of face recognition terminal
#GET /ISAPI/AccessControl/IdentityTerminal
#request_url = 'http://192.168.0.115:80/ISAPI/AccessControl/IdentityTerminal'
# Set the authentication information
#auth = requests.auth.HTTPDigestAuth('admin', 'sepl1234')
# Send the request and receive response
#response = requests.get(request_url, auth=auth)
# Output response content
#url = 'http://{}/ISAPI/AccessControl/IdentityTerminal'.format(server_ip)
# Returns XML

#6.2.2.1 Get the number of cards of a specified person
#GET /ISAPI/AccessControl/capabilities
#request_url = 'http://192.168.0.115:80/ISAPI/AccessControl/capabilities'
# Set the authentication information
#auth = requests.auth.HTTPDigestAuth('admin', 'sepl1234')
# Send the request and receive response
#response = requests.get(request_url, auth=auth)
# Output response content
#url = 'http://{}/ISAPI/AccessControl/capabilities'.format(server_ip)
# Returns XML


#6.2.2.2 Get the number of cards of a specified person
#GET /ISAPI/AccessControl/CardInfo/Count
#request_url = 'http://192.168.0.115:80/ISAPI/AccessControl/CardInfo/capabilities'
# Set the authentication information
#auth = requests.auth.HTTPDigestAuth('admin', 'sepl1234')
# Send the request and receive response
#response = requests.get(request_url, auth=auth)
# Output response content
#url = 'http://{}/ISAPI/AccessControl/CardInfo/capabilities'.format(server_ip)
# Returns JSON


#6.14.2.2 Person Search
#GET /ISAPI/AccessControl/UserInfo/capabilities
#request_url = 'http://192.168.0.115:80/ISAPI/AccessControl/UserInfo/capabilities'
# Set the authentication information
#auth = requests.auth.HTTPDigestAuth('admin', 'sepl1234')
# Send the request and receive response
#response = requests.get(request_url, auth=auth)
# Output response content
#url = 'http://{}/ISAPI/AccessControl/UserInfo/capabilities'.format(server_ip)
# Returns JSON


#6.14.2.2 Person Search
#GET /ISAPI/AccessControl/UserInfo/Count
#request_url = 'http://192.168.0.115:80/ISAPI/AccessControl/UserInfo/Count'
# Set the authentication information
#auth = requests.auth.HTTPDigestAuth('admin', 'sepl1234')
# Send the request and receive response
#response = requests.get(request_url, auth=auth)
# Output response content
#url = 'http://{}/ISAPI/AccessControl/UserInfo/Count'.format(server_ip)
# Returns JSON


# ----------------- METHOD = PUT ----------------------

#6.14.2.2 Person Search
#GET /ISAPI/AccessControl/UserInfo/Search
#request_url = 'http://192.168.0.115:80/ISAPI/AccessControl/UserInfo/Search'
# Set the authentication information
#auth = requests.auth.HTTPDigestAuth('admin', 'sepl1234')
# Send the request and receive response
#response = requests.get(request_url, auth=auth)
# Output response content
#url = 'http://{}/ISAPI/AccessControl/UserInfo/Search'.format(server_ip)
# Implemented with GET

#6.2.2.2 Get the number of cards of a specified person
#GET /ISAPI/AccessControl/CardInfo/Count
#request_url = 'http://192.168.0.115:80/ISAPI/AccessControl/CardInfo'
# Set the authentication information
#auth = requests.auth.HTTPDigestAuth('admin', 'sepl1234')
# Send the request and receive response
#response = requests.get(request_url, auth=auth)
# Output response content
#url = 'http://{}/ISAPI/AccessControl/CardInfo'.format(server_ip)
# Get Data with PUT

#6.14.2.2 Person Search
#GET /ISAPI/AccessControl/UserInfo
#request_url = 'http://192.168.0.115:80/ISAPI/AccessControl/UserInfo'
# Set the authentication information
#auth = requests.auth.HTTPDigestAuth('admin', 'sepl1234')
# Send the request and receive response
#response = requests.get(request_url, auth=auth)
# Output response content
#url = 'http://{}/ISAPI/AccessControl/CardInfo/count'.format(server_ip)
# Implemented in another program using GET

#6.2.2.2 Get the number of cards of a specified person
#GET /ISAPI/AccessControl/CardInfo/Count
#GET /ISAPI/AccessControl/CardInfo/Count?format=json
#request_url = 'http://192.168.0.115:80/ISAPI/AccessControl/CardInfo/count'
# Set the authentication information
#auth = requests.auth.HTTPDigestAuth('admin', 'sepl1234')
# Send the request and receive response
#response = requests.get(request_url, auth=auth)
# Output response content
#url = 'https://{}/ISAPI/AccessControl/CardInfo/Count?format=json'.format(server_ip)
# Implemented in another program

#Request Example
#http://192.168.1.108/cgi-bin/magicBox.cgi?action=getHardwareVersion
#url = 'http://{}/cgi-bin/magicBox.cgi?action=getHardwareVersion'.format(server_ip)



# Variable to store the parsed data
parsed_data = {}


# Function to strip namespace from tag
def strip_namespace(tag):
    return re.sub(r'\{.*?\}', '', tag)

# Function to convert an XML element into a dictionary
def xml_to_dict(element):
    data_dict = {}
    
    # If element has attributes, add them
    if element.attrib:
        data_dict['attributes'] = element.attrib

    # If element has children, recurse
    if list(element):
        data_dict['data'] = {}
        for child in element:
            tag = strip_namespace(child.tag)
            data_dict['data'][tag] = xml_to_dict(child)
    else:
        # If element has no children, just add its text value
        data_dict = element.text or ""
    
    return data_dict

# Function to parse XML string to dictionary
def parse_xml_to_dict(xml_string):
    root = ET.fromstring(xml_string)
    return {strip_namespace(root.tag): xml_to_dict(root)}

# Generalized function to extract fields from any unknown structure
def extract_fields(data_dict):
    extracted_data = {}

    # Recursive function to traverse through the dictionary
    def traverse_dict(d, parent_key=''):
        if isinstance(d, dict):
            for key, value in d.items():
                if isinstance(value, dict):
                    # Recur for nested dictionaries
                    traverse_dict(value, key)
                else:
                    # If value is not a dictionary, add it to the extracted data
                    extracted_data[key] = value
        elif isinstance(d, list):
            for item in d:
                # Traverse each item in a list (if needed)
                traverse_dict(item)
        else:
            # If it is a string or other base type, add directly
            extracted_data[parent_key] = d

    # Call recursive function starting from the root of the data_dict
    traverse_dict(data_dict)

    return extracted_data

# Function to parse XML string and convert it to JSON
def parse_and_convert_to_json(xml_data):
    try:
        # Parse the XML string
        root = ET.fromstring(xml_data)
        
        # Convert the XML tree to a dictionary
        xml_dict = {root.tag: xml_to_dict(root)}
        
        # Convert the dictionary to JSON format
        json_data = json.dumps(xml_dict, indent=4)
        
        return json_data

    except ET.ParseError as e:
        print("Error parsing XML:", e)
        return None


def parse_dahua_response(response_text):
    data_dict = {}
    current_path = None
    for line in response_text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            keys = key.split('.')

            # Recursively set keys in the dictionary
            d = data_dict
            for k in keys[:-1]:
                d = d.setdefault(k, {})
            
            # Convert values to appropriate types (int, float, bool)
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass
            
            d[keys[-1]] = value
    return data_dict


def sendDataToCloud(url,username,password,formatType,nvrdvrstate):

    try:
        # Send GET request to the Dahua NVR/DVR with HTTP Digest Authentication
        response = requests.get(url, auth=HTTPDigestAuth(username, password), verify=False, timeout=10)

#        print(response.text)


        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response as key-value pairs
            #response_text = response.text
            #parsed_data = parse_dahua_response(response_text)

            resposeFromBACS = formatType
            
            if resposeFromBACS == 0:

                json_output_raw = parse_and_convert_to_json(response.text)

                # Save JSON data to a Python variable for future use
                if json_output_raw:
                    saved_json_data = json_output_raw  # Save JSON string to a variable
#                    print("Parsed JSON data:")
#                    print(saved_json_data)
        
                # Step 1: Parse the XML string into a dictionary
                parsed_dict = parse_xml_to_dict(response.text)

                #print("Dictionary:----------------------------------------------------------------------------------")
                #data = json.loads(parsed_dict)
                #print(data)
                
                # Step 2: Extract key fields from the dictionary (automated for unknown structure)
                extracted_data = extract_fields(parsed_dict)

                # Output the result
#                print("Extracted Data:")
#                print(json.dumps(extracted_data, indent=4))


                # Optional: Store the extracted data in a Python variable
                attributes = extracted_data

                if nvrdvrstate == 0:

                    # Access specific information

                    try:
                        deviceName = attributes['deviceName']
                    except KeyError:
                        deviceName = 'Unknown Device'

                    try:
                        macAddress = attributes['macAddress']
                    except KeyError:
                        macAddress = 'Unknown macAddress'              

                    try:
                        subDeviceType = attributes['subDeviceType']
                    except KeyError:
                        subDeviceType = 'Unknown subDeviceType'              

                    try:
                        model = attributes['model']
                    except KeyError:
                        model = 'Unknown model'              

                    try:
                        serialNumber = attributes['serialNumber']
                    except KeyError:
                        serialNumber = 'Unknown Device'              

                    try:
                        firmwareVersion = attributes['firmwareVersion']
                    except KeyError:
                        firmwareVersion = 'Unknown firmwareVersion'              

                    try:
                        manufacturer = attributes['manufacturer']
                    except KeyError:
                        manufacturer = 'Unknown manufacturer'              

                    try:
                        RS485Num = attributes['RS485Num']                
                    except KeyError:
                        RS485Num = 'Unknown RS485Num'              

                    try:
                        deviceID = attributes['deviceID']                
                    except KeyError:
                        deviceID = 'Unknown deviceID'              

                    try:
                        deviceType = attributes['deviceType']                
                    except KeyError:
                        deviceType = 'Unknown deviceID'              

                    #macAddress = attributes['macAddress']
                
#                    print(deviceName)
#                    print(deviceID)
#                    print(model)
#                    print(serialNumber)
#                    print(macAddress)
#                    print(firmwareVersion)
#                    print(deviceType)
#                    print(RS485Num)                

                    payload = "{"
                    payload += "\"Hikvision_BACS_deviceName\":\"" + str(deviceName) + "\","
                    payload += "\"Hikvision_BACS_macAddress\":\"" + str(macAddress) + "\","
                    payload += "\"Hikvision_BACS_subDeviceType\":\"" + str(subDeviceType) + "\","
                    payload += "\"Hikvision_BACS_deviceID\":" + str(deviceID) + ","
                    payload += "\"Hikvision_BACS_model\":\"" + str(model) + "\","
                    payload += "\"Hikvision_BACS_serialNumber\":\"" + str(serialNumber) + "\","
                    payload += "\"Hikvision_BACS_firmwareVersion\":\"" + str(firmwareVersion) + "\","
                    payload += "\"Hikvision_BACS_deviceType\":\"" + str(deviceType) + "\","
                    payload += "\"Hikvision_BACS_manufacturer\":\"" + str(manufacturer) + "\","
                    payload += "\"Hikvision_BACS_RS485Num\":" + str(RS485Num)
                    payload += "}"

                    attributes = payload

                if nvrdvrstate == 2:
                    # Camera specific information

                    try:
                        camera = attributes['camera']
                    except KeyError:
                        camera = 'Unknown camera'              

                    try:
                        fingerPrintModule = attributes['fingerPrintModule']
                    except KeyError:
                        fingerPrintModule = 'Unknown fingerPrintModule'              

                    try:
                        MCUVersion = attributes['MCUVersion']
                    except KeyError:
                        MCUVersion = 'Unknown MCUVersion'              
                    
                
#                    print(camera) 
#                    print(fingerPrintModule)
#                    print(MCUVersion)

                    payload = "{"
                    payload += "\"Hikvision_BACS_camera\":\"" + str(camera) + "\","
                    payload += "\"Hikvision_BACS_fingerPrintModule\":\"" + str(fingerPrintModule) + "\","
                    payload += "\"Hikvision_BACS_MCUVersion\":\"" + str(MCUVersion) + "\""
                    payload += "}"

                    attributes = payload

                if nvrdvrstate == 6:

                    try:
                        timeZone = attributes['timeZone']
                    except KeyError:
                        timeZone = 'NA'              

                    try:
                        timeMode = attributes['timeMode']
                    except KeyError:
                        timeMode = 'NA'              
                    try:
                        version = attributes['version']
                    except KeyError:
                        version = 'NA'              
                    try:
                        localTime = attributes['localTime']
                    except KeyError:
                        localTime = 'NA'              
                    
                
#                    print(timeZone) 
#                    print(timeMode)
#                    print(version)                    
#                    print(localTime)

                    payload = "{"
                    payload += "\"Hikvision_BACS_timeZone\":\"" + str(timeZone) + "\","
                    payload += "\"Hikvision_BACS_timeMode\":\"" + str(timeMode) + "\","
                    payload += "\"Hikvision_BACS_version\":\"" + str(version) + "\","
                    payload += "\"Hikvision_BACS_localTime\":\"" + str(localTime) + "\""
                    payload += "}"

                    attributes = payload


                # Print the attributes
#                print("Attributes Dictionary:")
#                print(attributes)


                # Convert attributes to JSON string
                #attributes_json = json.dumps(attributes)

                attributes_json = attributes


                # Insert the JSON object into the database
                if logical_params_module.get_parameter("active_integration_hikvision_biometric") == 1:
                    insert_json_to_db(attributes_json)


                #ret= client1.publish("v1/devices/me/attributes",attributes_json)             #topic-v1/devices/me/telemetry
                print("Please check LATEST ATTRIBUTE field of your device")
                print(attributes_json)
    
                print("\n")


            elif resposeFromBACS == 1:
                
                if nvrdvrstate == 1:

                    # Parse the JSON string
                    data = json.loads(response.text)

                    # Storing individual parameters in variables
                    door_lock_status = data["AcsWorkStatus"]["doorLockStatus"][0]
                    door_status = data["AcsWorkStatus"]["doorStatus"][0]
                    magnetic_status = data["AcsWorkStatus"]["magneticStatus"][0]
                    anti_sneak_status = data["AcsWorkStatus"]["antiSneakStatus"]
                    host_anti_dismantle_status = data["AcsWorkStatus"]["hostAntiDismantleStatus"]
                    card_reader_online_status = data["AcsWorkStatus"]["cardReaderOnlineStatus"][0]
                    #card_reader_anti_dismantle_status = data["AcsWorkStatus"]["cardReaderAntiDismantleStatus"][0]   # Check
                    try:
                        card_reader_anti_dismantle_status = data["AcsWorkStatus"]["cardReaderAntiDismantleStatus"][0]
                    except KeyError:
                        card_reader_anti_dismantle_status = None  # or handle accordingly
#                        print("cardReaderAntiDismantleStatus not found in the response")
                    
                    card_reader_verify_mode = data["AcsWorkStatus"]["cardReaderVerifyMode"]
                    card_num = data["AcsWorkStatus"]["cardNum"]
                    net_status = data["AcsWorkStatus"]["netStatus"]
                    ezviz_status = data["AcsWorkStatus"]["ezvizStatus"]

                    # Printing variables to check
#                    print("door_lock_status:", door_lock_status)
#                    print("door_status:", door_status)
#                    print("magnetic_status:", magnetic_status)
#                    print("anti_sneak_status:", anti_sneak_status)
#                    print("host_anti_dismantle_status:", host_anti_dismantle_status)
#                    print("card_reader_online_status:", card_reader_online_status)
#                    print("card_reader_anti_dismantle_status:", card_reader_anti_dismantle_status)
#                    print("card_reader_verify_mode:", card_reader_verify_mode)
#                    print("card_num:", card_num)
#                    print("net_status:", net_status)
#                    print("ezviz_status:", ezviz_status)

                    payload = "{"
                    payload += "\"Hikvision_BACS_DoorLockStatus\":\"" + str(door_lock_status) + "\","
                    payload += "\"Hikvision_BACS_DoorStatus\":\"" + str(door_status) + "\","
                    payload += "\"Hikvision_BACS_hostAntiDismantleStatus\":\"" + str(host_anti_dismantle_status) + "\","
                    payload += "\"Hikvision_BACS_MagneticStatus\":\"" + str(magnetic_status) + "\""
                    payload += "}"

                    attributes = payload


                if nvrdvrstate == 11:
                    
                    payload = "{"
                    payload += "\"Hikvision_BACS_Hertbeat\":\"" + str(1) + "\""
                    payload += "}"



                if nvrdvrstate == 1:

                    # Print the attributes
#                    print("Telemetry Dictionary:")
#                    print(attributes)

                    # Convert attributes to JSON string
                    #attributes_json = json.dumps(attributes)

                    attributes_json = attributes
                    # Insert the JSON object into the database
                    if logical_params_module.get_parameter("active_integration_hikvision_biometric") == 1:                    
                        insert_json_to_db(attributes_json)
                    
                    #ret= client1.publish("v1/devices/me/attributes",attributes_json)             #topic-v1/devices/me/telemetry


                    print("Please check LATEST TELEMETRY field of your device")
                    print(attributes_json)                    
                else:

                    # Print the attributes
#                    print("Attributes Dictionary:")
#                    print(attributes)

                    # Convert attributes to JSON string
                    #attributes_json = json.dumps(attributes)

                    attributes_json = attributes

                    if logical_params_module.get_parameter("active_integration_hikvision_biometric") == 1:
                        insert_json_to_db(attributes_json)                    
                    #ret= client1.publish("v1/devices/me/attributes",attributes_json)             #topic-v1/devices/me/telemetry
                    
                    print("Please check LATEST ATTRIBUTE field of your device")
                    print(attributes_json)
    
                print("\n")




            # Convert to JSON format for further processing
            #json_response_data = json.dumps(parsed_data, indent=4)
            #print("Parsed response in JSON format:")
            #print(json_response_data)


            # Convert attributes to JSON string
            #attributes_json = json.dumps(json_response_data)


            #ret= client1.publish("v1/devices/me/attributes",json_response_data)             #topic-v1/devices/me/telemetry
            #print("Please check LATEST ATTRIBUTE field of your device")
            #print(json_response_data)
    
            #print("\n")


        elif response.status_code == 401:
            print("Authentication failed. Please check your credentials.")
        elif response.status_code == 403:
            print("Access forbidden. The digest authorization information is incorrect.")
        else:
            print("Failed to get a valid response. Status code:", response.status_code)

    except requests.RequestException as e:
        print("An error occurred:", e)

    # The parsed response is now stored in 'parsed_data' and 'json_response_data' and can be used for further processing.



def checkConnectionAndSendHRBtToCloud(url,username,password,formatType,nvrdvrstate):

    bacs_off = "bacs_off"
    
    try:
        # Send GET request to the Dahua NVR/DVR with HTTP Digest Authentication
        response = requests.get(url, auth=HTTPDigestAuth(username, password), verify=False, timeout=10)


        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response as key-value pairs
            #response_text = response.text
            #parsed_data = parse_dahua_response(response_text)


            bacs_off = "bacs_on"


        elif response.status_code == 401:
            print("Authentication failed. Please check your credentials.")
        elif response.status_code == 403:
            print("Access forbidden. The digest authorization information is incorrect.")
        else:
            print("Failed to get a valid response. Status code:", response.status_code)

    except requests.RequestException as e:
        print("An error occurred:", e)

    payload = "{"
    payload += "\"Hikvision_BACS_Heartbeat\":\"" + str(bacs_off) + "\""
    payload += "}"

    attributes = payload

    # Print the attributes
#    print("Telemetry Dictionary:")
#    print(attributes)


    attributes_json = attributes

    #print(attributes_json)
    if logical_params_module.get_parameter("active_integration_hikvision_biometric") == 1:            
        insert_json_to_db(attributes_json)
    #ret= client1.publish("v1/devices/me/telemetry",attributes_json)             #topic-v1/devices/me/telemetry
    print("Please check LATEST TELEMETRY field of your device")
    print(attributes_json)
    
    print("\n")

    # The parsed response is now stored in 'parsed_data' and 'json_response_data' and can be used for further processing.


# Update the payload with mandatory fields
payload1 = {
    "UserInfoSearchCond": {
        "searchID": "1",  # Unique ID for the search request
        "searchResultPosition": 0,  # Start position for the search results
        "maxResults": 10  # Maximum number of results to return
        # You can add more filters here, like "EmployeeNo", etc.
    }
}

# Update the payload with mandatory fields
payload2 = {
    "UserInfoSearchCond": {
        "searchID": "1",  # Unique ID for the search request
        "searchResultPosition": 0,  # Start position for the search results
        "maxResults": 10  # Maximum number of results to return
        # You can add more filters here, like "EmployeeNo", etc.
    }
}

# Payload for searching card information
payload3 = {
    "CardInfoSearchCond": {
        "searchID": "1",  # Unique ID for the search request
        "searchResultPosition": 0,  # Start position for the search results
        "maxResults": 10  # Maximum number of results to return
        # You can add specific filters for the card information search here
    }
}


# Update the payload with mandatory fields
payload4 = {
    "UserInfoSearchCond": {
        "searchID": "1",  # Unique ID for the search request
        "searchResultPosition": 0,  # Start position for the search results
        "maxResults": 10  # Maximum number of results to return
        # You can add more filters here, like "EmployeeNo", etc.
    }
}


def sendDataToCloudMethodPUT(url,username,password,payload,nvrdvrstate): 

    try:
        # Send a POST request with authentication and payload
        response = requests.post(url, 
                                 auth=HTTPDigestAuth(username, password), 
                                 data=json.dumps(payload),  # Convert dict to JSON
                                 headers={'Content-Type': 'application/json'},  # Set correct content type
                                 verify=False, 
                                 timeout=10)

        # Check if the request was successful
        if response.status_code == 200:
            # Try to parse the JSON response
            try:
                user_info = response.json()
                print("Response from the server:")
                print(json.dumps(user_info, indent=4))  # Pretty print the JSON response


                if nvrdvrstate == 10:
                    # Parse the JSON string
                    #data = json.loads(json_string)
                    
                    data = user_info
                    # Extracting information and storing it in individual variables
                    response_status = data["UserInfoSearch"]["responseStatusStrg"]
                    num_of_matches = data["UserInfoSearch"]["numOfMatches"]
                    search_id = data["UserInfoSearch"]["searchID"]
                    total_matches = data["UserInfoSearch"]["totalMatches"]

                    # Extract user info
                    user_info_list = data["UserInfoSearch"]["UserInfo"]

                    # Initialize lists to store individual user details
                    face_urls = []
                    names = []
                    employee_numbers = []
                    open_door_times = []
                    num_of_cards = []
                    genders = []
                    num_of_faces = []
                    local_ui_rights = []
                    max_open_door_times = []
                    door_rights = []
                    user_types = []
                    num_of_fps = []
                    valids = []
                    close_delay_enabled = []
                    right_plans = []
                    passwords = []

                    for user_info in user_info_list:
                        
                        try:
                            face_urls.append(user_info["faceURL"])
                        except KeyError:
                            print("Key 'faceURL' not found")
                        
                        #face_urls.append(user_info["faceURL"])
                        names.append(user_info["name"])
                        employee_numbers.append(user_info["employeeNo"])
                        open_door_times.append(user_info["openDoorTime"])
                        num_of_cards.append(user_info["numOfCard"])
                        genders.append(user_info["gender"])
                        num_of_faces.append(user_info["numOfFace"])
                        local_ui_rights.append(user_info["localUIRight"])
                        max_open_door_times.append(user_info["maxOpenDoorTime"])
                        door_rights.append(user_info["doorRight"])
                        user_types.append(user_info["userType"])
                        num_of_fps.append(user_info["numOfFP"])
                        valids.append(user_info["Valid"])
                        close_delay_enabled.append(user_info["closeDelayEnabled"])
                        right_plans.append(user_info["RightPlan"])
                        passwords.append(user_info["password"])

                    # Example of how to use the extracted variables
#                    print("Response Status:", response_status)
#                    print("Number of Matches:", num_of_matches)
#                    print("Search ID:", search_id)
#                    print("Total Matches:", total_matches)
                    #print("Face URLs:", face_urls)
#                    print("Names:", names)
#                    print("Employee Numbers:", employee_numbers)


                    # Extract user info
                    #user_info_list = data["UserInfoSearch"]["UserInfo"]

                    # Initialize total numOfCard
                    total_num_of_cards = 0

                    # Loop through each user and print numOfCard and compute the total
                    for i, user_info in enumerate(user_info_list):
                        num_of_card = user_info["numOfCard"]
                        total_num_of_cards += num_of_card
#                        print("User {}: numOfCard = {}".format(i + 1, num_of_card))

                    # Print the total number of numOfCard from all users
#                    print("Total numOfCard from all users:", total_num_of_cards)

                    payload = "{"
                    payload += "\"Hikvision_BACS_totalNumOfUsers\":\"" + str(num_of_matches) + "\","
                    payload += "\"Hikvision_BACS_totalNumOfCards\":\"" + str(total_num_of_cards) + "\""
                    payload += "}"

                    attributes = payload


                    # Print the attributes
#                    print("Attributes Dictionary:")
#                    print(attributes)


                    # Convert attributes to JSON string
                    #attributes_json = json.dumps(attributes)

                    attributes_json = attributes

                    if logical_params_module.get_parameter("active_integration_hikvision_biometric") == 1:
                        insert_json_to_db(attributes_json)
                    
                    #ret= client1.publish("v1/devices/me/attributes",attributes_json)             #topic-v1/devices/me/telemetry
                    print("Please check LATEST ATTRIBUTE field of your device")
                    print(attributes_json)


                if nvrdvrstate == 100: # nvrdvrstate is = 10 with limited scope of information collection 

                    # Parse JSON string
                    #data = json.loads(user_info)
                    data = user_info

                    # Extracting individual variables from the JSON
                    response_status = data['UserInfoSearch']['responseStatusStrg']
                    num_of_matches = data['UserInfoSearch']['numOfMatches']
                    search_id = data['UserInfoSearch']['searchID']
                    total_matches = data['UserInfoSearch']['totalMatches']
                    user_info = data['UserInfoSearch']['UserInfo']

                    # Extracting details for each user
                    user1 = user_info[0]
                    user2 = user_info[1]
                    user3 = user_info[2]

                    # Example: Extract details for user 1
                    user1_face_url = user1['faceURL']
                    user1_name = user1['name']
                    user1_gender = user1['gender']
                    user1_validity_start = user1['Valid']['beginTime']
                    user1_validity_end = user1['Valid']['endTime']
                    user1_employee_no = user1['employeeNo']

                    # Example: Print the extracted variables
#                    print("Response Status:", response_status)
#                    print("Number of Matches:", num_of_matches)
#                    print("Search ID:", search_id)
#                    print("Total Matches:", total_matches)

#                    print("\nUser 1 Details:")
#                    print("Name:", user1_name)
#                    print("Face URL:", user1_face_url)
#                    print("Gender:", user1_gender)
#                    print("Validity Start:", user1_validity_start)
#                    print("Validity End:", user1_validity_end)
#                    print("Employee No:", user1_employee_no)


                # Convert attributes to JSON string
                #attributes_json = json.dumps(user_info)

                #ret= client1.publish("v1/devices/me/attributes",attributes_json)             #topic-v1/devices/me/telemetry
                #print("Please check LATEST ATTRIBUTE field of your device")
                #print(attributes_json)
    
                print("\n")
                
            except ValueError:  # In Python 2.7, JSONDecodeError is not available, use ValueError
                print("Failed to decode JSON response.")
        else:
            print("Failed to retrieve user info. Status code: {}".format(response.status_code))
            print(response.text)

    except requests.exceptions.RequestException as e:
        print("An error occurred while making the request: {}".format(e))



def initExternalDevice():
    
#    print(" Initialise Devices ")

    # Sleep briefly to reduce CPU usage
    time.sleep(30.0)

    device_type = 'HikvisionBioMetric1'
    server_ip, username, password = get_device_credentials(device_type)

    def sendParameters():

        def checkHBRT(): 
            # Initialize the camera client
            try:
                url = 'http://{}/ISAPI/System/deviceInfo'.format(server_ip)                         #4.1.4
                formatType = 0
                checkConnectionAndSendHRBtToCloud(url,username,password, formatType, nvrdvrstate)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass
        
        def sendTime():

            time.sleep(30.0)        
            nvrdvrstate = 6
            # Initialize the camera client
            try:
                url = 'http://{}/ISAPI/System/time'.format(server_ip)            
                formatType = 0
                sendDataToCloud(url,username,password, formatType, nvrdvrstate)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass
        
        checkHBRT()
        sendTime()

    sendParameters()


nvrdvrstate = 0

import time
from threading import Lock

# Define tasks (Task1 to Task10 as examples)
def Task1():
#    print "Task1 executed at", time.strftime('%Y-%m-%d %H:%M:%S')

    def SubTask():
        def SubSubTask():
            
            device_type = 'HikvisionBioMetric1'
            server_ip, username, password = get_device_credentials(device_type)

            nvrdvrstate = 0
            # Initialize the camera client
            try:
                url = 'http://{}/ISAPI/System/deviceInfo'.format(server_ip)                         #4.1.4
                formatType = 0
                sendDataToCloud(url,username,password, formatType, nvrdvrstate)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        SubSubTask()            
    SubTask()    


def Task2():
#    print "Task2 executed at", time.strftime('%Y-%m-%d %H:%M:%S')

    def SubTask():
        def SubSubTask():
            
            device_type = 'HikvisionBioMetric1'
            server_ip, username, password = get_device_credentials(device_type)

            nvrdvrstate = 1
            # Initialize the camera client
            try:
                url = 'http://{}/ISAPI/AccessControl/AcsWorkStatus'.format(server_ip)               #10.2.3.5
                formatType = 1
                sendDataToCloud(url,username,password, formatType, nvrdvrstate)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        SubSubTask()            
    SubTask()    

def Task3():
#    print "Task3 executed at", time.strftime('%Y-%m-%d %H:%M:%S')

    def SubTask():
        def SubSubTask():
            device_type = 'HikvisionBioMetric1'
            server_ip, username, password = get_device_credentials(device_type)

            nvrdvrstate = 2
            # Initialize the camera client
            try:
                url = 'http://{}/ISAPI/AccessControl/IdentityTerminal'.format(server_ip)            #10.2.7.20
                formatType = 0
                sendDataToCloud(url,username,password, formatType, nvrdvrstate)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        SubSubTask()            
    SubTask()    

def Task4():
#    print "Task4 executed at", time.strftime('%Y-%m-%d %H:%M:%S')

    def SubTask():
        def SubSubTask():
            device_type = 'HikvisionBioMetric1'
            server_ip, username, password = get_device_credentials(device_type)

            nvrdvrstate = 10                                                                        
            # Initialize the camera client
            try:
                url = 'http://{}/ISAPI/AccessControl/UserInfo/Search?format=json'.format(server_ip)
                sendDataToCloudMethodPUT(url,username,password, payload4, nvrdvrstate)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        SubSubTask()            
    SubTask()    
    

def Task5():
#    print "Task5 executed at", time.strftime('%Y-%m-%d %H:%M:%S')

    def SubTask():
        def SubSubTask():
            device_type = 'HikvisionBioMetric1'
            server_ip, username, password = get_device_credentials(device_type)

            # Initialize the camera client
            try:
                url = 'http://{}/ISAPI/System/deviceInfo'.format(server_ip)                         #4.1.4
                formatType = 0
                checkConnectionAndSendHRBtToCloud(url,username,password, formatType, nvrdvrstate)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        SubSubTask()            
    SubTask()    
    

def Task6():
#    print "Task6 executed at", time.strftime('%Y-%m-%d %H:%M:%S')

    def SubTask():
        def SubSubTask():
            device_type = 'HikvisionBioMetric1'
            server_ip, username, password = get_device_credentials(device_type)

            nvrdvrstate = 6
            # Initialize the camera client
            try:
                url = 'http://{}/ISAPI/System/time'.format(server_ip)            
                formatType = 0
                sendDataToCloud(url,username,password, formatType, nvrdvrstate)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        SubSubTask()            
    SubTask()    


def Task7():
    print "Task7 executed at", time.strftime('%Y-%m-%d %H:%M:%S')

def Task8():
    print "Task8 executed at", time.strftime('%Y-%m-%d %H:%M:%S')

def Task9():
    print "Task9 executed at", time.strftime('%Y-%m-%d %H:%M:%S')

def Task10():
    print "Task10 executed at", time.strftime('%Y-%m-%d %H:%M:%S')

# Map task names to functions dynamically
task_functions = {}
for i in range(1, 11):
    task_name = "Task{}".format(i)
    task_functions[task_name] = globals()[task_name]

def get_task_configurations(configurations, min_gap):
    """
    Accept task configurations and predefined gap between executions.
    :param configurations: List of dictionaries with task name and interval.
                           Example: [{"name": "Task1", "interval": 60}, {"name": "Task2", "interval": 120}]
    :param min_gap: Minimum gap in seconds between executing two tasks.
    :return: Tasks list with scheduling metadata and minimum gap.
    """
    tasks = []
    for config in configurations:
        task_name = config["name"]
        interval = config["interval"]
        if task_name not in task_functions:
#            print "Error: Task {} is not defined!".format(task_name)
            continue
        tasks.append({"name": task_name, "function": task_functions[task_name], "interval": interval, "next_run": 0})
    
    return tasks, min_gap


def main():
    # Example configuration passed as parameters
    #task_configs = [
    #    {"name": "Task1", "interval": 350},
    #    {"name": "Task2", "interval": 300},
    #    {"name": "Task4", "interval": 370},
    #    {"name": "Task5", "interval": 300},        
    #    {"name": "Task6", "interval": 600}
    #]

    # Example configuration passed as parameters
    task_configs = [
        {"name": "Task1", "interval": 21600},
        {"name": "Task2", "interval": 300},
        {"name": "Task4", "interval": 21600},
        {"name": "Task5", "interval": 300},        
        {"name": "Task6", "interval": 600}
    ]
    
    min_gap = 30  # Minimum gap between two task executions (in seconds)

    base_time = 1.0  # Base time for scheduling
    tasks, min_gap = get_task_configurations(task_configs, min_gap)
    execution_lock = Lock()
    last_execution_time = 0

    initExternalDevice()

    while True:
        current_time = time.time()

        for task in tasks:
            # Check if it's time to execute the task and if enough gap has passed
            if current_time >= task["next_run"] and current_time - last_execution_time >= min_gap:
                with execution_lock:
                    task["function"]()  # Execute the task function
                    last_execution_time = time.time()  # Update last execution time
                    # Calculate the next run time for the task
                    task["next_run"] = current_time + task["interval"]

        time.sleep(base_time)  # Sleep for base time before checking the schedule again


if __name__ == "__main__":
    main()
    watchdog.reset()  # Reset watchdog after 30min
