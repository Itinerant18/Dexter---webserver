# -*- coding: utf-8 -*-
# !/usr/local/bin/python

import requests
from requests.auth import HTTPDigestAuth
import warnings
import json
import paho.mqtt.client as paho  		    #mqtt library
import time

import threading
import os
import sys

from buffer_manager import insert_json_to_db
import device_parameters_module


import logical_params_module
# Initialize the database
logical_params_module.initialize_database()


class SoftwareWatchdog:
    def __init__(self, timeout=3600):
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
#                print "Watchdog timeout! Restarting software..."
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
                    "Module Reboot": "Dahua Info",
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

#        print "Watchdog timeout! Restarting software..."
    
        # Restart the script
        python = sys.executable if sys.executable else "/usr/bin/python2"
        os.execl(python, python, *sys.argv)
  
# Initialize software watchdog with 3600-second timeout
watchdog = SoftwareWatchdog(timeout=3600)



device_type = 'DahuaNVR1'
devices = device_parameters_module.get_device_parameters(device_type)
ipaddress = devices[0][2]
userid = devices[0][3]
passowrd = devices[0][4]


resolutions = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
fps_values = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

nvrdvrstate = 0

#ACCESS_TOKEN='yzaVD1gEyOtSk4sGPrk4'
#broker='www.dexterhms.com'
#port=1883 					    #data listening port


#def on_publish(client,userdata,result):             #create function for callback
#    print("data published to thingsboard \n")
#    pass

#client1= paho.Client("control1")                    #create client object
#client1.on_publish = on_publish                     #assign function to callback
#client1.username_pw_set(ACCESS_TOKEN)               #access token from thingsboard device
#client1.connect(broker,port,keepalive=60)           #establish connection

# Suppress the SSL warning
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

# Replace with the actual IP address or domain of your Dahua NVR/DVR
#server_ip = '192.168.0.108'
server_ip = ipaddress

# Request Params (key=value format in URL)

#6.1.3 Get Storage Device Information
#Get all the storage device information .
#Request URL http://<server>/cgi-bin/storageDevice.cgi?action=getDeviceAllInfo
#Method GET
#Request Params ( key=value format in URL )
#Name Type R/O Description Example
#Request Example
#http://192.168.1.108/cgi-bin/storageDevice.cgi?action=getDeviceAllInfo
#url = 'http://{}/cgi-bin/storageDevice.cgi?action=getDeviceAllInfo'.format(server_ip)

#4.6.11 Get Machine Name
#Get the device machine name.
#Request URL http://<server>/cgi-bin/magicBox.cgi?action=getMachineName
#Method GET
#Request Params ( none )
#Request Example
#http://192.168.1.108/cgi-bin/magicBox.cgi?action=getMachineName
#url = 'http://{}/cgi-bin/magicBox.cgi?action=getMachineName'.format(server_ip)          


#4.6.12 Get System Information
#Get the system information of the device.
#Request URL http://<server>/cgi-bin/magicBox.cgi?action=getSystemInfoNew
#Method GET
#Request Params ( none )
#Request Example
#http://192.168.1.108/cgi-bin/magicBox.cgi?action=getSystemInfoNew
#url = 'http://{}/cgi-bin/magicBox.cgi?action=getSystemInfoNew'.format(server_ip)


#4.6.10 Get Serial Number of Device
#Get the serial number of the device.
#Request URL http://<server>/cgi-bin/magicBox.cgi?action=getSerialNo
#Method GET
#Request Params ( none )
#Request Example
#http://192.168.1.108/cgi-bin/magicBox.cgi?action=getSerialNo
#url = 'http://{}/cgi-bin/magicBox.cgi?action=getSerialNo'.format(server_ip)

#4.6.8 Get Device Type
#Get the device type displayed (instead of the real type).
#Request URL http://<server>/cgi-bin/magicBox.cgi?action=getDeviceType
#Method GET
#Request Params ( none )
#Request Example
#http://192.168.1.108/cgi-bin/magicBox.cgi?action=getDeviceType
#url = 'http://{}/cgi-bin/magicBox.cgi?action=getDeviceType'.format(server_ip)


#4.6.9 Get Hardware Version
#Get the device hardware version information.
#Request URL http://<server>/cgi-bin/magicBox.cgi?action=getHardwareVersion
#Method GET
#Request Params ( none )
#Request Example
#http://192.168.1.108/cgi-bin/magicBox.cgi?action=getHardwareVersion
#url = 'http://{}/cgi-bin/magicBox.cgi?action=getHardwareVersion'.format(server_ip)

#4.6.2 Get Current Time
#Request URL http://<server>/cgi-bin/global.cgi?action=getCurrentTime
#Method GET
#Request Params ( none)
#Name Type R/O Description Example
#Request Example
#http://192.168.1.108/cgi-bin/global.cgi?action=getCurrentTime
#Response Params ( key=value format in body )
#Name Type R/O Description Example
#result char[20] O The time format is "Y-M-D H-m-S". It's
#not be effected by Locales. TimeFormat
#in SetLocalesConfig.
#2011-7-3 21:02:32
#Response Example
#result=2011-7-3 21:02:32
#url = 'http://{}/cgi-bin/global.cgi?action=getCurrentTime'.format(server_ip)


#4.9.4 Get Alarm Input Channels
#Request URL http://<server>/cgi-bin/alarm.cgi?action=getInSlots
#Method GET
#Request Params ( none)
#Name Type R/O Description Example
#Request Example
#http://192.168.1.108/cgi-bin/alarm.cgi?action=getInSlots
#url = 'http://{}/cgi-bin/alarm.cgi?action=getInSlots'.format(server_ip)

#4.6.25 Acquiring All Available Resources
#Customer requests to obtain camera information, such as MAC address and SN, through CGI
#commands.
#Request URL http://<server>/cgi-bin/LogicDeviceManager.cgi?action=getCameraAll
#Method GET
#Request Params ( key=value format in Url )
#Name Type R/O Description Example
#Request Example
#http://192.168.1.108/cgi-bin/LogicDeviceManager.cgi?action=getCameraAll
#url = 'http://{}/cgi-bin/LogicDeviceManager.cgi?action=getCameraAll'.format(server_ip)

# Credentials for authentication
#username = 'admin'
#password = 'sepl1984'

username = userid
password = passowrd

# Variable to store the parsed data
parsed_data = {}

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

def sendDataToCloud(url,username,password):
    try:
        # Send GET request to the Dahua NVR/DVR with HTTP Digest Authentication
        response = requests.get(url, auth=HTTPDigestAuth(username, password), verify=False, timeout=10)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response as key-value pairs
            response_text = response.text
            
            parsed_data = parse_dahua_response(response_text)

#            print(parsed_data)            

            #json_response_loads = json.loads(parsed_data)

            #print(json_response_loads)
        
            # Convert to JSON format for further processing
            json_response_data = json.dumps(parsed_data, indent=4)
#            print("Parsed response in JSON format:")
#            print(json_response_data)

            #json_response_loads = json.loads(json_response_data)

            #json_object = json.loads(parsed_data)
            #print(json_object)


            json_string_no_newlines_t = json_response_data.replace('\n', '')

            json_string_no_newlines_n = process_json(json_string_no_newlines_t)

            global nvrdvrstate
            
            if nvrdvrstate == 0:
                json_string_no_newlines = getDeviceAllInfo(json_string_no_newlines_n)
            elif nvrdvrstate == 1:
                json_string_no_newlines = machineName(json_string_no_newlines_n)
            elif nvrdvrstate == 2:
                json_string_no_newlines = SystemInfoNew(json_string_no_newlines_n)
            #elif nvrdvrstate == 3:
            #    json_string_no_newlines = SerialNo(json_string_no_newlines_n)
            elif nvrdvrstate == 5:
                json_string_no_newlines = hardwareVersion(json_string_no_newlines_n)
            elif nvrdvrstate == 6:
                json_string_no_newlines = currentTime(json_string_no_newlines_n)
            elif nvrdvrstate == 8:
                json_string_no_newlines = cameraAll(json_string_no_newlines_n)
            elif nvrdvrstate == 9:
                json_string_no_newlines = firmwareVersion(json_string_no_newlines_n)
            elif nvrdvrstate == 10:
                json_string_no_newlines = manufacturer(json_string_no_newlines_n)

            if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
                insert_json_to_db(json_string_no_newlines)
            print("Please check LATEST ATTRIBUTE field of your device")
            print(json_string_no_newlines)
    
            print("\n")


        elif response.status_code == 401:
            print("Authentication failed. Please check your credentials.")
        elif response.status_code == 403:
            print("Access forbidden. The digest authorization information is incorrect.")
        else:
            print("Failed to get a valid response. Status code:", response.status_code)
    except requests.RequestException as e:
        print("An error occurred:", e)

    # The parsed response is now stored in 'parsed_data' and 'json_response_data' and can be used for further processing.        


def sendDataToCloud_video(url,username,password):
    try:
        # Send GET request to the Dahua NVR/DVR with HTTP Digest Authentication
        response = requests.get(url, auth=HTTPDigestAuth(username, password), verify=False, timeout=10)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response as key-value pairs
            response_text = response.text
            
            parsed_data = parse_dahua_response(response_text)

#            print(parsed_data)            

            #json_response_loads = json.loads(parsed_data)

            #print(json_response_loads)
        
            # Convert to JSON format for further processing
            json_response_data = json.dumps(parsed_data, indent=4)
#            print("Parsed response in JSON format:")
#            print(json_response_data)

            #json_response_loads = json.loads(json_response_data)

            #json_object = json.loads(parsed_data)
            #print(json_object)


#            json_string_no_newlines_t = json_response_data.replace('\n', '')

#            json_string_no_newlines = process_json(json_string_no_newlines_t)

        
#            insert_json_to_db(json_string_no_newlines)



            # Parse the JSON string
#            data = json.loads(json_response_data)
#            print(data)             

            # Navigate to the required fields
#            resolution = data["table"]["Encode[1]"]["MainFormat[0]"]["Video"]["resolution"]
#            fps = data["table"]["Encode[1]"]["MainFormat[0]"]["Video"]["FPS"]

            # Store the values in variables
#            resolution_value = resolution
#            fps_value = fps

            # Output the captured values
#            print("Resolution:", resolution_value)
#            print("FPS:", fps_value)


            # Parse the JSON string
            data = json.loads(json_response_data)

            # Create a dictionary to store resolutions and FPS values for each Encode[i]
            encode_data = {}
            encode_output = []  # List to store output for later use
            
            # Loop through Encode[1] to Encode[16]
            for i in range(0, 16):
                encode_key = "Encode[{}]".format(i)
    
                # Check if the key exists in the data
                if encode_key in data["table"]:
                    try:
                        resolution = data["table"][encode_key]["MainFormat[0]"]["Video"]["resolution"]
                        fps = data["table"][encode_key]["MainFormat[0]"]["Video"]["FPS"]
                        # Store the resolution and FPS in the dictionary
                        encode_data[encode_key] = {"resolution": resolution, "FPS": fps}
                    except KeyError as e:
                        print("Missing data for {}: {}".format(encode_key, e))
                else:
                    print("{} not found in the data".format(encode_key))

            # Output the captured values for all encodes
            for encode_key, video_data in encode_data.items():
                print("{} - Resolution: {}, FPS: {}".format(encode_key, video_data['resolution'], video_data['FPS']))

            #encode_data[encode_key] = {"resolution": resolution, "FPS": fps}

            # Example: Access a specific encode's data later on
            encode_to_check = "Encode[1]"
            if encode_to_check in encode_data:
                print("\nSpecific data for {}: ".format(encode_to_check))
#                print("Resolution: {}".format(encode_data[encode_to_check]['resolution']))
#                print("FPS: {}".format(encode_data[encode_to_check]['FPS']))

            
#            print("-------------------") 
            print(encode_data[encode_to_check]['resolution'])
#            print(encode_data[encode_to_check]['FPS'])



            global resolutions
            global fps_values

           
            encode_to_check = "Encode[0]"
            resolutions[0] = encode_data[encode_to_check]['resolution']
            fps_values[0] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[1]"
            resolutions[1] = encode_data[encode_to_check]['resolution']
            fps_values[1] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[2]"
            resolutions[2] = encode_data[encode_to_check]['resolution']
            fps_values[2] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[3]"
            resolutions[3] = encode_data[encode_to_check]['resolution']
            fps_values[3] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[4]"
            resolutions[4] = encode_data[encode_to_check]['resolution']
            fps_values[4] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[5]"
            resolutions[5] = encode_data[encode_to_check]['resolution']
            fps_values[5] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[6]"
            resolutions[6] = encode_data[encode_to_check]['resolution']
            fps_values[6] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[7]"
            resolutions[7] = encode_data[encode_to_check]['resolution']
            fps_values[7] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[8]"
            resolutions[8] = encode_data[encode_to_check]['resolution']
            fps_values[8] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[9]"
            resolutions[9] = encode_data[encode_to_check]['resolution']
            fps_values[9] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[10]"
            resolutions[10] = encode_data[encode_to_check]['resolution']
            fps_values[10] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[11]"
            resolutions[11] = encode_data[encode_to_check]['resolution']
            fps_values[11] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[12]"
            resolutions[12] = encode_data[encode_to_check]['resolution']
            fps_values[12] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[13]"
            resolutions[13] = encode_data[encode_to_check]['resolution']
            fps_values[13] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[14]"
            resolutions[14] = encode_data[encode_to_check]['resolution']
            fps_values[14] = encode_data[encode_to_check]['FPS']

            encode_to_check = "Encode[15]"
            resolutions[15] = encode_data[encode_to_check]['resolution']
            fps_values[15] = encode_data[encode_to_check]['FPS']


            #payload = "{"
            #payload += "\"resolutions\":\"" + str(resolutions[0]) + "\","
            #payload += "\"fps\":\"" + str(fps_values[0]) + "\""
            #payload += "}"
            
            payload = "{"
            
            payload += "\"DahuaNVR_Encode[0]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[0]) + "\","
            payload += "\"fps\": \"" + str(fps_values[0]) + "\""
            payload += "},"
            payload += "\"DahuaNVR_Encode[1]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[1]) + "\","
            payload += "\"fps\": \"" + str(fps_values[1]) + "\""
            payload += "},"
           
            payload += "\"DahuaNVR_Encode[2]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[2]) + "\","
            payload += "\"fps\": \"" + str(fps_values[2]) + "\""
            payload += "},"
            payload += "\"DahuaNVR_Encode[3]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[3]) + "\","
            payload += "\"fps\": \"" + str(fps_values[3]) + "\""
            payload += "},"

            payload += "\"DahuaNVR_Encode[4]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[4]) + "\","
            payload += "\"fps\": \"" + str(fps_values[4]) + "\""
            payload += "},"
            payload += "\"DahuaNVR_Encode[5]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[5]) + "\","
            payload += "\"fps\": \"" + str(fps_values[5]) + "\""
            payload += "},"

            payload += "\"DahuaNVR_Encode[6]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[6]) + "\","
            payload += "\"fps\": \"" + str(fps_values[6]) + "\""
            payload += "},"
            payload += "\"DahuaNVR_Encode[7]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[7]) + "\","
            payload += "\"fps\": \"" + str(fps_values[7]) + "\""
            payload += "},"

            payload += "\"DahuaNVR_Encode[8]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[8]) + "\","
            payload += "\"fps\": \"" + str(fps_values[8]) + "\""
            payload += "},"
            payload += "\"DahuaNVR_Encode[9]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[9]) + "\","
            payload += "\"fps\": \"" + str(fps_values[9]) + "\""
            payload += "},"

            payload += "\"DahuaNVR_Encode[10]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[10]) + "\","
            payload += "\"fps\": \"" + str(fps_values[10]) + "\""
            payload += "},"
            payload += "\"DahuaNVR_Encode[11]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[11]) + "\","
            payload += "\"fps\": \"" + str(fps_values[11]) + "\""
            payload += "},"

            payload += "\"DahuaNVR_Encode[12]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[12]) + "\","
            payload += "\"fps\": \"" + str(fps_values[12]) + "\""
            payload += "},"
            payload += "\"DahuaNVR_Encode[13]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[13]) + "\","
            payload += "\"fps\": \"" + str(fps_values[13]) + "\""
            payload += "},"

            payload += "\"DahuaNVR_Encode[14]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[14]) + "\","
            payload += "\"fps\": \"" + str(fps_values[14]) + "\""
            payload += "},"
            payload += "\"DahuaNVR_Encode[15]\": {"
            payload += "\"resolutions\": \"" + str(resolutions[15]) + "\","
            payload += "\"fps\": \"" + str(fps_values[15]) + "\""
            payload += "}"

            payload += "}"


            # Create the payload with Encode[0] to Encode[15], each having unique resolution and FPS
            #payload = {}
            #for i in range(16):
            #    payload["Encode[{}]".format(i)] = {
            #        "resolution": resolutions[i],
            #        "FPS": fps_values[i]
            #    }

            print(payload)

#            insert_json_to_db(payload)

            # Convert attributes to JSON string
            #attributes_json = json.dumps(json_response_data)

            #ret= client1.publish("v1/devices/me/telemetry",json_response_data)             #topic-v1/devices/me/telemetry
            #ret= client1.publish("v1/devices/me/attributes",json_response_data)             #topic-v1/devices/me/telemetry
#            print("Please check LATEST ATTRIBUTE field of your device")
#            print(json_string_no_newlines)
    
            print("\n")


        elif response.status_code == 401:
            print("Authentication failed. Please check your credentials.")
        elif response.status_code == 403:
            print("Access forbidden. The digest authorization information is incorrect.")
        else:
            print("Failed to get a valid response. Status code:", response.status_code)
    except requests.RequestException as e:
        print("An error occurred:", e)

    # The parsed response is now stored in 'parsed_data' and 'json_response_data' and can be used for further processing.        



def sendDataToCloud_video3(url, username, password):
    #response = requests.get(url, auth=(username, password))
    response = requests.get(url, auth=HTTPDigestAuth(username, password), verify=False, timeout=10)
    try:
        data = response.json()  # Assuming the response is in JSON format
#        print("Data received:", data)  # Print the full response for debugging

        # Check if 'table' exists in the data
        if "table" in data:
            resolution = data["table"]["Encode[1]"]["MainFormat[0]"]["Video"]["resolution"]
            fps = data["table"]["Encode[1]"]["MainFormat[0]"]["Video"]["FPS"]
#            print("Resolution:", resolution)
#            print("FPS:", fps)
        else:
            print("Error: 'table' key not found in the data")
    except json.JSONDecodeError as e:
        print("Failed to decode JSON:", str(e))
    except KeyError as e:
        print("Missing key in data:", str(e))

# Function to clean and reformat JSON string
def process_json(json_string):
    # Split to get the actual JSON part
    json_string = json_string.split("('Consumed and processed JSON:', u'")[0]
    
    try:
        # Load JSON to remove extra spaces and newlines
        json_object = json.loads(json_string)
        
        # Re-dump to a single-line JSON
        clean_json = json.dumps(json_object)
        
        return clean_json
    except ValueError as e:
        return "Invalid JSON format: " + str(e)


def getDeviceAllInfo(json_data):

    # Parse the JSON data
    data = json.loads(json_data)

    # Access each detail individually
    detail_0 = data["list"]["info[0]"]["Detail[0]"]
    detail_1 = data["list"]["info[0]"]["Detail[1]"]
    detail_2 = data["list"]["info[0]"]["Detail[2]"]
    detail_3 = data["list"]["info[0]"]["Detail[3]"]

    # Access specific fields
    total_bytes_0 = detail_0["TotalBytes"]
    total_bytes_1 = detail_1["TotalBytes"]
    total_bytes_2 = detail_2["TotalBytes"]
    total_bytes_3 = detail_3["TotalBytes"]    
    
    
    path_0 = detail_0["Path"]
    path_2 = detail_2["Path"]
    path_3 = detail_3["Path"]


    try:
        path_1 = detail_1["Path"]
    except KeyError:
        path_1 = 'NA'
    

    try:
        used_bytes_2 = detail_2["UsedBytes"]
    except KeyError:
        used_bytes_2 = 'NA'

    try:
        used_bytes_1 = detail_1["UsedBytes"]
    except KeyError:
        used_bytes_1 = 'NA'

    try:
        used_bytes_0 = detail_0["UsedBytes"]
    except KeyError:
        used_bytes_0 = 'NA'

    try:
        used_bytes_3 = detail_3["UsedBytes"]
    except KeyError:
        used_bytes_3 = 'NA'
    
    type_3 = detail_3["Type"]

    # Print the values
#    print("Dahua_NVR_capacity in Detail[0]:", total_bytes_0)
#    print("Dahua_NVR_capacity in Detail[0]:", total_bytes_1)
#    print("Dahua_NVR_capacity in Detail[0]:", total_bytes_2)
#    print("Dahua_NVR_capacity in Detail[0]:", total_bytes_3)

#    print("Dahua_NVR_NoOfHDDSlots Path in Detail[1]:", path_1)
#    print("Dahua_NVR_NoOfHDDSlots Path in Detail[1]:", path_0)
#    print("Dahua_NVR_NoOfHDDSlots Path in Detail[1]:", path_2)
#    print("Dahua_NVR_NoOfHDDSlots Path in Detail[1]:", path_3)

#    print("Dahua_NVR_freeSpace UsedBytes in Detail[2]:", used_bytes_2)
#    print("Dahua_NVR_freeSpace UsedBytes in Detail[2]:", used_bytes_1)
#    print("Dahua_NVR_freeSpace UsedBytes in Detail[2]:", used_bytes_0)
#    print("Dahua_NVR_freeSpace UsedBytes in Detail[2]:", used_bytes_3)        
    
#    print("Type in Detail[3]:", type_3)


    # Create a dictionary for each NVR detail
    payload = {
        "Dahua_NVR_Details[0]": {
            "Dahua_NVR_capacity": str(total_bytes_0),
            "Dahua_NVR_NoOfHDDSlots": str(path_0),
            "Dahua_NVR_freeSpace": str(used_bytes_0)
        },
        "Dahua_NVR_Details[1]": {
            "Dahua_NVR_capacity": str(total_bytes_1),
            "Dahua_NVR_NoOfHDDSlots": str(path_1),
            "Dahua_NVR_freeSpace": str(used_bytes_1)
        },
        "Dahua_NVR_Details[2]": {
            "Dahua_NVR_capacity": str(total_bytes_2),
            "Dahua_NVR_NoOfHDDSlots": str(path_2),
            "Dahua_NVR_freeSpace": str(used_bytes_2)
        },
        "Dahua_NVR_Details[3]": {
            "Dahua_NVR_capacity": str(total_bytes_3),
            "Dahua_NVR_NoOfHDDSlots": str(path_3),
            "Dahua_NVR_freeSpace": str(used_bytes_3)
        }
    }

    # Wrap in a parent dictionary under "deviceAllInfo"
    deviceAllInfo = {
        "Dahua_NVR_deviceAllInfo": payload
    }

    # Convert to JSON string (optional)
    json_deviceAllInfo = json.dumps(deviceAllInfo)

    print(json_deviceAllInfo)
    return json_deviceAllInfo
   

def machineName(json_data):

    # Parse the JSON data
    parsed_data = json.loads(json_data)

    # Extract the value associated with the key "name"
    name_value = parsed_data['name']

    payload = "{"
    payload += "\"Dahua_NVR_deviceName\":\"" + str(name_value) + "\""
    payload += "}"


    # Print the extracted value
    print(payload)
    return(payload)


def SystemInfoNew(json_data):

    # Parse the JSON data
    parsed_data = json.loads(json_data)

    # Extract values from the JSON object
    update_serial = parsed_data['updateSerial']
    serial_number = parsed_data['serialNumber']
    device_type = parsed_data['deviceType']
    processor = parsed_data['processor']

    # Print the extracted values
#    print("Update Serial:", update_serial)
#    print("Serial Number:", serial_number)
#    print("Device Type:", device_type)
#    print("Processor:", processor)

    payload = "{"
    payload += "\"Dahua_NVR_Model\":\"" + str(update_serial) + "\","
    payload += "\"Dahua_NVR_SerialNumber\":\"" + str(serial_number) + "\","
    payload += "\"Dahua_NVR_DeviceType\":\"" + str(device_type) + "\","
    payload += "\"Dahua_NVR_Processor\":\"" + str(processor) + "\""
    payload += "}"

    # Print the extracted value
    print(payload)
    return(payload)


def SerialNo(json_data):

    # Parse the JSON data
    parsed_data = json.loads(json_data)

    # Extract the value associated with the key "sn"
    serial_number = parsed_data['sn']

    # Print the extracted value
#    print("Serial Number:", serial_number)


    payload = "{"
    payload += "\"Dahua_NVR_SerialNumber\":\"" + str(serial_number) + "\""
    payload += "}"


    # Print the extracted value
    print(payload)
    return(payload)


def hardwareVersion(json_data):

    # Parse the JSON data
    parsed_data = json.loads(json_data)

    # Extract the value associated with the key "version"
    version = parsed_data['version']

    # Print the extracted value
#    print("Version:", version)

    payload = "{"
    payload += "\"Dahua_NVR_Hardware_Version\":\"" + str(version) + "\""
    payload += "}"


    # Print the extracted value
    print(payload)
    return(payload)



def currentTime(json_data):

    # Parse the JSON data
    parsed_data = json.loads(json_data)

    # Extract the value associated with the key "result"
    result = parsed_data['result']

    # Split the result into date and time
    date, time = result.split()

    # Print the extracted date and time
#    print("Date:", date)
#    print("Time:", time)

    payload = "{"
    payload += "\"Dahua_NVR_Date\":\"" + str(date) + "\","
    payload += "\"Dahua_NVR_Time\":\"" + str(time) + "\""
    payload += "}"

    # Print the extracted value
    print(payload)
    return(payload)



def cameraAll(json_data):

    # Load JSON data
    data = json.loads(json_data)

    # Access and store individual elements
    camera_0 = data.get("camera[0]", {})

    # DeviceInfo elements
    device_info = camera_0.get("DeviceInfo", {})
    address_0 = device_info.get("Address")
    name_0 = device_info.get("Name")


    # Access and store individual elements
    camera_1 = data.get("camera[1]", {})

    # DeviceInfo elements
    device_info = camera_1.get("DeviceInfo", {})
    address_1 = device_info.get("Address")
    name_1 = device_info.get("Name")


    # Access and store individual elements
    camera_2 = data.get("camera[2]", {})

    # DeviceInfo elements
    device_info = camera_2.get("DeviceInfo", {})
    address_2 = device_info.get("Address")
    name_2 = device_info.get("Name")


    # Access and store individual elements
    camera_3 = data.get("camera[3]", {})

    # DeviceInfo elements
    device_info = camera_3.get("DeviceInfo", {})
    address_3 = device_info.get("Address")
    name_3 = device_info.get("Name")


    # Access and store individual elements
    camera_4 = data.get("camera[4]", {})

    # DeviceInfo elements
    device_info = camera_4.get("DeviceInfo", {})
    address_4 = device_info.get("Address")
    name_4 = device_info.get("Name")


    # Access and store individual elements
    camera_5 = data.get("camera[5]", {})

    # DeviceInfo elements
    device_info = camera_5.get("DeviceInfo", {})
    address_5 = device_info.get("Address")
    name_5 = device_info.get("Name")


    # Access and store individual elements
    camera_6 = data.get("camera[6]", {})

    # DeviceInfo elements
    device_info = camera_6.get("DeviceInfo", {})
    address_6 = device_info.get("Address")
    name_6 = device_info.get("Name")


    # Access and store individual elements
    camera_7 = data.get("camera[7]", {})

    # DeviceInfo elements
    device_info = camera_7.get("DeviceInfo", {})
    address_7 = device_info.get("Address")
    name_7 = device_info.get("Name")

    # Access and store individual elements
    camera_8 = data.get("camera[8]", {})

    # DeviceInfo elements
    device_info = camera_8.get("DeviceInfo", {})
    address_8 = device_info.get("Address")
    name_8 = device_info.get("Name")

    # Access and store individual elements
    camera_9 = data.get("camera[9]", {})

    # DeviceInfo elements
    device_info = camera_9.get("DeviceInfo", {})
    address_9 = device_info.get("Address")
    name_9 = device_info.get("Name")

    # Access and store individual elements
    camera_10 = data.get("camera[10]", {})

    # DeviceInfo elements
    device_info = camera_10.get("DeviceInfo", {})
    address_10 = device_info.get("Address")
    name_10 = device_info.get("Name")

    # Access and store individual elements
    camera_11 = data.get("camera[11]", {})

    # DeviceInfo elements
    device_info = camera_11.get("DeviceInfo", {})
    address_11 = device_info.get("Address")
    name_11 = device_info.get("Name")


    # Access and store individual elements
    camera_12 = data.get("camera[12]", {})

    # DeviceInfo elements
    device_info = camera_12.get("DeviceInfo", {})
    address_12 = device_info.get("Address")
    name_12 = device_info.get("Name")


    # Access and store individual elements
    camera_13 = data.get("camera[13]", {})

    # DeviceInfo elements
    device_info = camera_13.get("DeviceInfo", {})
    address_13 = device_info.get("Address")
    name_13 = device_info.get("Name")


    # Access and store individual elements
    camera_14 = data.get("camera[14]", {})

    # DeviceInfo elements
    device_info = camera_14.get("DeviceInfo", {})
    address_14 = device_info.get("Address")
    name_14 = device_info.get("Name")


    # Access and store individual elements
    camera_15 = data.get("camera[15]", {})

    # DeviceInfo elements
    device_info = camera_15.get("DeviceInfo", {})
    address_15 = device_info.get("Address")
    name_15 = device_info.get("Name")


    # Store these elements in a dictionary or another data structure
    #extracted_data = {
    #    "Address": address,
    #    "Name": name
    #}

    # Print each extracted element
    #for key, value in extracted_data.items():
    #    print("{}: {}".format(key, value))


    global resolutions
    global fps_values

    # Create a dictionary for each NVR detail
    payload = {
        "0": {
            "Dahua_NVR_Address": str(address_0),
            "Dahua_NVR_Resolutions": str(resolutions[0]),
            "Dahua_NVR_FPS_Values": str(fps_values[0]),
            "Dahua_NVR_Name": str(name_0)
        },
        "1": {
            "Dahua_NVR_Address": str(address_1),
            "Dahua_NVR_Resolutions": str(resolutions[1]),
            "Dahua_NVR_FPS_Values": str(fps_values[1]),
            "Dahua_NVR_Name": str(name_1)
        },
        "2": {
            "Dahua_NVR_Address": str(address_2),
            "Dahua_NVR_Resolutions": str(resolutions[2]),
            "Dahua_NVR_FPS_Values": str(fps_values[2]),
            "Dahua_NVR_Name": str(name_2)
        },
        "3": {
            "Dahua_NVR_Address": str(address_3),
            "Dahua_NVR_Resolutions": str(resolutions[3]),
            "Dahua_NVR_FPS_Values": str(fps_values[3]),
            "Dahua_NVR_Name": str(name_3)
        },
        "4": {
            "Dahua_NVR_Address": str(address_4),
            "Dahua_NVR_Resolutions": str(resolutions[4]),
            "Dahua_NVR_FPS_Values": str(fps_values[4]),
            "Dahua_NVR_Name": str(name_4)
        },
        "5": {
            "Dahua_NVR_Address": str(address_5),
            "Dahua_NVR_Resolutions": str(resolutions[5]),
            "Dahua_NVR_FPS_Values": str(fps_values[5]),
            "Dahua_NVR_Name": str(name_5)
        },
        "6": {
            "Dahua_NVR_Address": str(address_6),
            "Dahua_NVR_Resolutions": str(resolutions[6]),
            "Dahua_NVR_FPS_Values": str(fps_values[6]),
            "Dahua_NVR_Name": str(name_6)
        },
        "7": {
            "Dahua_NVR_Address": str(address_7),
            "Dahua_NVR_Resolutions": str(resolutions[7]),
            "Dahua_NVR_FPS_Values": str(fps_values[7]),
            "Dahua_NVR_Name": str(name_7)
        },
        "8": {
            "Dahua_NVR_Address": str(address_8),
            "Dahua_NVR_Resolutions": str(resolutions[8]),
            "Dahua_NVR_FPS_Values": str(fps_values[8]),
            "Dahua_NVR_Name": str(name_8)
        },
        "9": {
            "Dahua_NVR_Address": str(address_9),
            "Dahua_NVR_Resolutions": str(resolutions[9]),
            "Dahua_NVR_FPS_Values": str(fps_values[9]),
            "Dahua_NVR_Name": str(name_9)
        },
        "10": {
            "Dahua_NVR_Address": str(address_10),
            "Dahua_NVR_Resolutions": str(resolutions[10]),
            "Dahua_NVR_FPS_Values": str(fps_values[10]),
            "Dahua_NVR_Name": str(name_10)
        },
        "11": {
            "Dahua_NVR_Address": str(address_11),
            "Dahua_NVR_Resolutions": str(resolutions[11]),
            "Dahua_NVR_FPS_Values": str(fps_values[11]),
            "Dahua_NVR_Name": str(name_11)
        },
        "12": {
            "Dahua_NVR_Address": str(address_12),
            "Dahua_NVR_Resolutions": str(resolutions[12]),
            "Dahua_NVR_FPS_Values": str(fps_values[12]),
            "Dahua_NVR_Name": str(name_12)
        },
        "13": {
            "Dahua_NVR_Address": str(address_13),
            "Dahua_NVR_Resolutions": str(resolutions[13]),
            "Dahua_NVR_FPS_Values": str(fps_values[13]),
            "Dahua_NVR_Name": str(name_13)
        },
        "14": {
            "Dahua_NVR_Address": str(address_14),
            "Dahua_NVR_Resolutions": str(resolutions[14]),
            "Dahua_NVR_FPS_Values": str(fps_values[14]),
            "Dahua_NVR_Name": str(name_14)
        },
        "15": {
            "Dahua_NVR_Address": str(address_15),
            "Dahua_NVR_Resolutions": str(resolutions[15]),
            "Dahua_NVR_FPS_Values": str(fps_values[15]),
            "Dahua_NVR_Name": str(name_15)
        }
    }

    # Wrap in a parent dictionary under "deviceAllInfo"
    cameraAll = {
        "Dahua_NVR_cameraInfo": payload
    }

    # Convert to JSON string (optional)
    json_deviceAllInfo = json.dumps(cameraAll)

    print(json_deviceAllInfo)
    return json_deviceAllInfo



def firmwareVersion(json_data):

    # Parse JSON data
    data = json.loads(json_data)

    # Extract the full version string
    version_string = data.get("version")

    # Split the version string to get individual elements
    version_number, build_info = version_string.split(",build:")

    # Print the separated elements
#    print("Version Number:", version_number)
#    print("Build Date:", build_info)

    payload = "{"
    payload += "\"Dahua_NVR_Firmware_Version\":\"" + str(version_number) + "\""
    payload += "}"


    # Print the extracted value
    print(payload)
    return(payload)


def manufacturer(json_data):

    # Parse JSON data
    data = json.loads(json_data)

    # Extract the "vendor" field
    vendor = data.get("vendor")

    # Print the extracted element
#    print("Vendor:", vendor)

    payload = "{"
    payload += "\"Dahua_NVR_Manufacturer\":\"" + str(vendor) + "\""
    payload += "}"


    # Print the extracted value
    print(payload)
    return(payload)



def initExternalDevice():
    
    print(" Initialise Devices ")

    # Sleep briefly to reduce CPU usage
    time.sleep(30.0)

    
    def sendParameters():

        def checkHBRT(): 
        
            #url = 'http://{}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'.format(server_ip)
            url = 'http://{}/cgi-bin/magicBox.cgi?action=getVendor'.format(server_ip)
            #sendDataToCloud(url,username,password)
            
            try:
                # Send GET request to the Dahua NVR/DVR with HTTP Digest Authentication
                response = requests.get(url, auth=HTTPDigestAuth(username, password), verify=False, timeout=10)

                # Check if the request was successful
                if response.status_code == 200:

                    Heartbeat_t = "DahuaNVR_on"

                    payload = "{"
                    payload += "\"DahuaNVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                    payload += "}"

                    # Now you can use channel_details_json to send to another API
                    attributes_json = payload

                    if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
                        insert_json_to_db(attributes_json)
                    print("Please check LATEST ATTRIBUTE field of your device")
                    print(attributes_json)

                elif response.status_code == 401:
                    print("Authentication failed. Please check your credentials.")
                elif response.status_code == 403:
                    print("Access forbidden. The digest authorization information is incorrect.")
                else:
                    print("Failed to get a valid response. Status code:", response.status_code)
                    
            except requests.RequestException as e:
                
                print("An error occurred:", e)

                Heartbeat_t = "DahuaNVR_off"
                
                payload = "{"
                payload += "\"DahuaNVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                payload += "}"

                # Now you can use channel_details_json to send to another API
                attributes_json = payload

                if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
                    insert_json_to_db(attributes_json)
                    
                print("Please check LATEST ATTRIBUTE field of your device")
                print(attributes_json)
                pass
        
        def sendTime():
            time.sleep(30.0)        

            global nvrdvrstate
            nvrdvrstate = 6
            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/global.cgi?action=getCurrentTime'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        checkHBRT()
        sendTime()

    sendParameters()


#insert_json_to_db(attributes_json)
nvrdvrstate = 0

# Define custom intervals (in seconds) for each condition
#intervals = [90, 120, 150, 180, 210, 240, 270, 300, 330, 360, 60]  # Adjust these intervals as needed for each condition
intervals = [21600, 86400, 86400, 21600, 86400, 600, 21600, 86400, 86400, 21600, 300]  # Adjust these intervals as needed for each condition

# Initialize last execution timestamps for each condition
start_time = time.time()
last_run_times = [start_time for _ in intervals]

if __name__ == '__main__':

    initExternalDevice()
    
    # Infinite loop
    while True:
        # Get the current time
        current_time = time.time()

        # Condition 1
        if current_time - last_run_times[0] >= intervals[0]:
#            print("Executing Condition 1")
            last_run_times[0] = current_time
            
            nvrdvrstate = 0            
            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/storageDevice.cgi?action=getDeviceAllInfo'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        # Condition 2
        if current_time - last_run_times[1] >= intervals[1]:
#            print("Executing Condition 2")
            last_run_times[1] = current_time

            nvrdvrstate = 1
            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/magicBox.cgi?action=getMachineName'.format(server_ip)          
                sendDataToCloud(url,username,password)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        # Condition 3
        if current_time - last_run_times[2] >= intervals[2]:
#            print("Executing Condition 3")
            last_run_times[2] = current_time

            nvrdvrstate = 2            
            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/magicBox.cgi?action=getSystemInfoNew'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:

#                print("Error while initializing the camera client:", e)
                pass

        # Condition 4
        if current_time - last_run_times[3] >= intervals[3]:
#            print("Executing Condition 4")
            last_run_times[3] = current_time
            
            nvrdvrstate = 4
            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'.format(server_ip)
                sendDataToCloud_video(url,username,password)
                #sendDataToCloud(url,username,password)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        # Condition 5
        if current_time - last_run_times[4] >= intervals[4]:
#            print("Executing Condition 5")
            last_run_times[4] = current_time

            nvrdvrstate = 5
            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/magicBox.cgi?action=getHardwareVersion'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        # Condition 6
        if current_time - last_run_times[5] >= intervals[5]:
#            print("Executing Condition 6")
            last_run_times[5] = current_time

            nvrdvrstate = 6
            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/global.cgi?action=getCurrentTime'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        # Condition 7
        if current_time - last_run_times[6] >= intervals[6]:
#            print("Executing Condition 7")
            last_run_times[6] = current_time

            nvrdvrstate = 8
            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/LogicDeviceManager.cgi?action=getCameraAll'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        # Condition 8
        if current_time - last_run_times[7] >= intervals[7]:
#            print("Executing Condition 8")
            last_run_times[7] = current_time

            nvrdvrstate = 9
            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/magicBox.cgi?action=getSoftwareVersion'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        # Condition 9
        if current_time - last_run_times[8] >= intervals[8]:
#            print("Executing Condition 9")
            last_run_times[8] = current_time

            nvrdvrstate = 10
            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/magicBox.cgi?action=getVendor'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        # Condition 10
        if current_time - last_run_times[9] >= intervals[9]:
#            print("Executing Condition 10")
            last_run_times[9] = current_time

            nvrdvrstate = 11
            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'.format(server_ip)
                sendDataToCloud_video(url,username,password)
                #sendDataToCloud(url,username,password)
            except Exception as e:
#                print("Error while initializing the camera client:", e)
                pass

        # Condition 11
        if current_time - last_run_times[10] >= intervals[10]:
#            print("Executing Condition 11")
            last_run_times[10] = current_time

            #url = 'http://{}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'.format(server_ip)
            url = 'http://{}/cgi-bin/magicBox.cgi?action=getVendor'.format(server_ip)
            #sendDataToCloud(url,username,password)
            
            try:
                # Send GET request to the Dahua NVR/DVR with HTTP Digest Authentication
                response = requests.get(url, auth=HTTPDigestAuth(username, password), verify=False, timeout=10)

                # Check if the request was successful
                if response.status_code == 200:

                    Heartbeat_t = "DahuaNVR_on"

                    payload = "{"
                    payload += "\"DahuaNVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                    payload += "}"

                    # Now you can use channel_details_json to send to another API
                    attributes_json = payload
                    if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
                        insert_json_to_db(attributes_json)
                    print("Please check LATEST ATTRIBUTE field of your device")
                    print(attributes_json)

                elif response.status_code == 401:
                    print("Authentication failed. Please check your credentials.")
                elif response.status_code == 403:
                    print("Access forbidden. The digest authorization information is incorrect.")
                else:
                    print("Failed to get a valid response. Status code:", response.status_code)
                    
            except requests.RequestException as e:
                
                print("An error occurred:", e)

                Heartbeat_t = "DahuaNVR_off"
                
                payload = "{"
                payload += "\"DahuaNVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                payload += "}"

                # Now you can use channel_details_json to send to another API
                attributes_json = payload
                if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
                    insert_json_to_db(attributes_json)
                print("Please check LATEST ATTRIBUTE field of your device")
                print(attributes_json)
                pass

        # Sleep briefly to reduce CPU usage
        time.sleep(1.0)

    
    while True:
        
        if nvrdvrstate == 0:

            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/storageDevice.cgi?action=getDeviceAllInfo'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass

            nvrdvrstate = 1
            
        elif nvrdvrstate == 1:


            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/magicBox.cgi?action=getMachineName'.format(server_ip)          
                sendDataToCloud(url,username,password)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass

            nvrdvrstate = 2
            
        elif nvrdvrstate == 2:


            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/magicBox.cgi?action=getSystemInfoNew'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:

                print("Error while initializing the camera client:", e)
                pass

            nvrdvrstate = 4
            
        elif nvrdvrstate == 4: 

            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'.format(server_ip)
                sendDataToCloud_video(url,username,password)
                #sendDataToCloud(url,username,password)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass

            nvrdvrstate = 5

            # Initialize the Dahua NVR DVR
            #try:
            #    url = 'http://{}/cgi-bin/magicBox.cgi?action=getSerialNo'.format(server_ip)
            #    sendDataToCloud(url,username,password)
            #except Exception as e:
            #    print("Error while initializing the camera client:", e)
            #    pass
            
        #elif nvrdvrstate == 4: # Not Required
        #    nvrdvrstate = 5

            # Initialize the Dahua NVR DVR
        #    try:
        #        url = 'http://{}/cgi-bin/magicBox.cgi?action=getSerialNo'.format(server_ip)
        #        sendDataToCloud(url,username,password)
        #    except Exception as e:
        #        print("Error while initializing the camera client:", e)
        #        pass
            
        elif nvrdvrstate == 5:

            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/magicBox.cgi?action=getHardwareVersion'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass
            nvrdvrstate = 6

        elif nvrdvrstate == 6:

            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/global.cgi?action=getCurrentTime'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass

            nvrdvrstate = 8
            
        elif nvrdvrstate == 7: # Not Required
            nvrdvrstate = 7

            # Initialize the Dahua NVR DVR
            #try:
            #    url = 'http://{}/cgi-bin/alarm.cgi?action=getInSlots'.format(server_ip)
            #    sendDataToCloud(url,username,password)
            #except Exception as e:
            #    print("Error while initializing the camera client:", e)
            #    pass

        elif nvrdvrstate == 8:

            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/LogicDeviceManager.cgi?action=getCameraAll'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass

            nvrdvrstate = 9
            
        elif nvrdvrstate == 9:

            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/magicBox.cgi?action=getSoftwareVersion'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass
            
            nvrdvrstate = 10

        elif nvrdvrstate == 10:

            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/magicBox.cgi?action=getVendor'.format(server_ip)
                sendDataToCloud(url,username,password)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass

            nvrdvrstate = 12

        elif nvrdvrstate == 11:

            # Initialize the Dahua NVR DVR
            try:
                url = 'http://{}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'.format(server_ip)
                sendDataToCloud_video(url,username,password)
                #sendDataToCloud(url,username,password)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass

            nvrdvrstate = 11

        elif nvrdvrstate == 12:
            nvrdvrstate = 0

            # Initialize the Dahua NVR DVR
            try:
                
                url = 'http://{}/cgi-bin/configManager.cgi?action=getConfig&name=Encode'.format(server_ip)
                
                Heartbeat_t = "DahuaNVR_on"

                payload = "{"
                payload += "\"DahuaNVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                payload += "}"

                # Now you can use channel_details_json to send to another API
                attributes_json = payload
                if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
                    insert_json_to_db(attributes_json)
                print("Please check LATEST ATTRIBUTE field of your device")
                print(attributes_json)

            except Exception as e:
                
                print("Error while initializing the camera client:", e)

                Heartbeat_t = "DahuaNVR_off"

                payload = "{"
                payload += "\"DahuaNVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                payload += "}"

                # Now you can use channel_details_json to send to another API
                attributes_json = payload
                if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
                    insert_json_to_db(attributes_json)
                print("Please check LATEST ATTRIBUTE field of your device")
                print(attributes_json)

                pass

        time.sleep(1800) #Sec 3600
        watchdog.reset(3600)  # Reset watchdog after 1Hr    


