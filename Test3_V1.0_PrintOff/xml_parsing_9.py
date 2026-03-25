# -*- coding: utf-8 -*-
# !/usr/local/bin/python


import requests
from hikvisionapi import Client
import xml.etree.ElementTree as ET
import paho.mqtt.client as paho  		    #mqtt library
import json
import re
import time

import threading 
import os
import sys

from buffer_manager import insert_json_to_db
import device_parameters_module  

from requests.auth import HTTPDigestAuth
from requests.exceptions import ConnectionError


class SoftwareWatchdog:
    def __init__(self, timeout=129600):
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
                    "Module Reboot": "Hik NVR Info",
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
  
# Initialize software watchdog with 129600-second timeout
watchdog = SoftwareWatchdog(timeout=129600)


ACCESS_TOKEN='1ZUF4oSdRNchyIgRQsPz'
broker='www.dexterhms.com'
port=1883 					    #data listening port

# Define a global variable for the desired structure
camera_info = {
    "cameraInfo": {}
}

#def on_publish(client,userdata,result):             #create function for callback
#    print("data published to thingsboard \n")
#    pass

#client1= paho.Client("control1")                    #create client object
#client1.on_publish = on_publish                     #assign function to callback
#client1.username_pw_set(ACCESS_TOKEN)               #access token from thingsboard device
#client1.connect(broker,port,keepalive=60)           #establish connection

device_type = 'HikvisionNVR1'
devices = device_parameters_module.get_device_parameters(device_type)
ipaddress = devices[0][2]
userid = devices[0][3]
passowrd = devices[0][4]

print(ipaddress)
print(userid)
print(passowrd)

#cam = Client('http://192.168.0.109', 'admin', 'sepl1984')
#cam = Client('http://'+ipaddress, userid, passowrd)


import logical_params_module
# Initialize the database
logical_params_module.initialize_database()


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


def extract_fields_hdd_1(data_dict):
    extracted_data = []

    # Recursive function to traverse through the dictionary
    def traverse_dict(d):
        if isinstance(d, dict):
            current_data = {}
            for key, value in d.items():
                if isinstance(value, dict):
                    # Recur for nested dictionaries
                    current_data[key] = traverse_dict(value)
                elif isinstance(value, list):
                    # Process each item in the list
                    current_data[key] = [traverse_dict(item) for item in value]
                else:
                    # Add the value directly if it is not a nested dictionary or list
                    current_data[key] = value
            return current_data
        elif isinstance(d, list):
            return [traverse_dict(item) for item in d]
        else:
            # If it's a base type, return it directly
            return d

    # Check for 'hddList' key and process each hdd entry individually
    if isinstance(data_dict, dict) and 'hddList' in data_dict:
        hdd_list = data_dict['hddList'].get('hdds', [])
        for hdd in hdd_list:
            extracted_data.append(traverse_dict(hdd))
    else:
        extracted_data = traverse_dict(data_dict)

    return extracted_data

def extract_fields_hdd(data_dict):
    extracted_data = []

    # Traverse and extract data specifically for each hard disk
    if "hddList" in data_dict and "hdds" in data_dict["hddList"]:
        hdd_list = data_dict["hddList"]["hdds"]
        for hdd in hdd_list:
            hdd_data = {}
            for key, value in hdd.items():
                hdd_data[key] = value
            extracted_data.append(hdd_data)
    
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



def parse_and_convert_to_json_hdd(xml_data):
    try:
        # Parse the XML string
        root = ET.fromstring(xml_data)
        
        # Iterate through each <hdd> element and extract details
        hdd_list = []
        for hdd in root.findall('{http://www.hikvision.com/ver20/XMLSchema}hdd'):
            hdd_info = {
                'id': hdd.find('{http://www.hikvision.com/ver20/XMLSchema}id').text,
                'hddName': hdd.find('{http://www.hikvision.com/ver20/XMLSchema}hddName').text,
                'hddPath': hdd.find('{http://www.hikvision.com/ver20/XMLSchema}hddPath').text,
                'hddType': hdd.find('{http://www.hikvision.com/ver20/XMLSchema}hddType').text,
                'status': hdd.find('{http://www.hikvision.com/ver20/XMLSchema}status').text,
                'capacity': hdd.find('{http://www.hikvision.com/ver20/XMLSchema}capacity').text,
                'freeSpace': hdd.find('{http://www.hikvision.com/ver20/XMLSchema}freeSpace').text,
                'property': hdd.find('{http://www.hikvision.com/ver20/XMLSchema}property').text
            }
            hdd_list.append(hdd_info)
        
        # Create the JSON data structure
        json_data = {
            "hddList": {
                "version": root.attrib.get("version", ""),
                "hdds": hdd_list
            }
        }
        
        return json.dumps(json_data, indent=4)
    
    except ET.ParseError as e:
        print("Error parsing XML:", e)
        return None


# XML string input (replace this with any unknown XML string)
xml_string = '''<StreamingChannelList version="1.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
    <StreamingChannel version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
        <enabled>true</enabled>
        <channelName>102</channelName>
        <Audio>
            <audioInputChannelID>1</audioInputChannelID>
            <enabled>true</enabled>
            <audioCompressionType>G.711ulaw</audioCompressionType>
        </Audio>
        <Transport>
            <ControlProtocolList>
                <ControlProtocol>
                    <streamingTransport>RTSP</streamingTransport>
                </ControlProtocol>
            </ControlProtocolList>
        </Transport>
        <id>102</id>
        <Video>
            <enabled>true</enabled>
            <dynVideoInputChannelID>1</dynVideoInputChannelID>
            <maxFrameRate>0</maxFrameRate>
            <SmartCodec>
                <enabled>true</enabled>
            </SmartCodec>
            <vbrLowerCap>32</vbrLowerCap>
            <snapShotImageType>JPEG</snapShotImageType>
            <GovLength>50</GovLength>
            <fixedQuality>60</fixedQuality>
            <vbrUpperCap>512</vbrUpperCap>
            <videoScanType>progressive</videoScanType>
            <videoCodecType>H.265</videoCodecType>
            <videoResolutionHeight>360</videoResolutionHeight>
            <videoQualityControlType>VBR</videoQualityControlType>
            <videoResolutionWidth>640</videoResolutionWidth>
        </Video>
    </StreamingChannel>
</StreamingChannelList>'''


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
payload4a = {
    "UserInfoSearchCond": {
        "searchID": "1",  # Unique ID for the search request
        "searchResultPosition": 0,  # Start position for the search results
        "maxResults": 10  # Maximum number of results to return
        # You can add more filters here, like "EmployeeNo", etc.
    }
}



def dict_to_xml(tag, d):
    """Convert a dictionary to an XML string with a single root tag."""
    element = ET.Element(tag)
    for key, val in d.items():
        child = ET.Element(key)
        child.text = str(val)
        element.append(child)
    return ET.tostring(element, encoding='utf8', method='xml')

# Sample payload dictionary
payload4 = {
    "SearchID": "12345",
    "MaxResults": "10",
    "StartTime": "2024-11-01T00:00:00Z",
    "EndTime": "2024-11-01T23:59:59Z"
}


def sendDataToCloudMethodPUT(url, username, password, payload, nvrdvrstate):
    try:
        # Send a POST request with authentication and payload
        response = requests.post(url,
                                 auth=HTTPDigestAuth(username, password),
                                 data=payload,  # Send XML payload
                                 headers={'Content-Type': 'application/xml'},  # Set content type as XML
                                 verify=False,
                                 timeout=10)

        # Check if the request was successful
        if response.status_code == 200:
            try:
                print("Response from the server:")
                print(response.text)  # Print the raw XML response
            except Exception as e:
                print("Failed to process response. Error: {}".format(e))
        else:
            print("Failed to retrieve user info. Status code: {}".format(response.status_code))
            print(response.text)
    except requests.exceptions.RequestException as e:
        print("An error occurred while making the request: {}".format(e))



def sendDataToCloudMethodPUT_old(url,username,password,payload,nvrdvrstate): 

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



                if nvrdvrstate == 100:
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
                    print("Response Status:", response_status)
                    print("Number of Matches:", num_of_matches)
                    print("Search ID:", search_id)
                    print("Total Matches:", total_matches)
                    #print("Face URLs:", face_urls)
                    print("Names:", names)
                    print("Employee Numbers:", employee_numbers)


                    # Extract user info
                    #user_info_list = data["UserInfoSearch"]["UserInfo"]

                    # Initialize total numOfCard
                    total_num_of_cards = 0

                    # Loop through each user and print numOfCard and compute the total
                    for i, user_info in enumerate(user_info_list):
                        num_of_card = user_info["numOfCard"]
                        total_num_of_cards += num_of_card
                        print("User {}: numOfCard = {}".format(i + 1, num_of_card))

                    # Print the total number of numOfCard from all users
                    print("Total numOfCard from all users:", total_num_of_cards)

                    payload = "{"
                    payload += "\"Hikvision_BACS_totalNumOfUsers\":\"" + str(num_of_matches) + "\","
                    payload += "\"Hikvision_BACS_totalNumOfCards\":\"" + str(total_num_of_cards) + "\""
                    payload += "}"

                    attributes = payload


                    # Print the attributes
                    print("Attributes Dictionary:")
                    print(attributes)


                    # Convert attributes to JSON string
                    #attributes_json = json.dumps(attributes)

                    attributes_json = attributes


                    if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1: 
                        insert_json_to_db(attributes_json)
                    
                    #ret= client1.publish("v1/devices/me/attributes",attributes_json)             #topic-v1/devices/me/telemetry
                    print("Please check LATEST ATTRIBUTE field of your device")
                    print(attributes_json)


                if nvrdvrstate == 1001: # nvrdvrstate is = 10 with limited scope of information collection 

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
                    print("Response Status:", response_status)
                    print("Number of Matches:", num_of_matches)
                    print("Search ID:", search_id)
                    print("Total Matches:", total_matches)

                    print("\nUser 1 Details:")
                    print("Name:", user1_name)
                    print("Face URL:", user1_face_url)
                    print("Gender:", user1_gender)
                    print("Validity Start:", user1_validity_start)
                    print("Validity End:", user1_validity_end)
                    print("Employee No:", user1_employee_no)


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


def hickConnect(response):
    
    #Program for Printing Raw Data

    # Parse the XML and convert it to JSON
    #json_output = parse_and_convert_to_json(xml_data)
    json_output_raw = parse_and_convert_to_json(response)

    # Save JSON data to a Python variable for future use
    if json_output_raw:
        saved_json_data = json_output_raw  # Save JSON string to a variable
        print("Parsed JSON data:")
        print(saved_json_data)


    # Parse the JSON string into a Python dictionary
    #parsed_json_raw = json.loads(json_output_raw)

    # Navigate to the "data" portion
    #data_section_raw = parsed_json_raw["{http://www.hikvision.com/ver20/XMLSchema}StreamingChannelList"]["data"]

    # Save the data section in a separate variable
    #saved_data_raw = data_section_raw

    # Print the extracted data part
    #print("Extracted 'data' part:")
    #print(json.dumps(saved_data_raw, indent=4))


    #Program for Data sending to Cloud


    # Step 1: Parse the XML string into a dictionary
    parsed_dict = parse_xml_to_dict(response)

    # Step 2: Extract key fields from the dictionary (automated for unknown structure)
    extracted_data = extract_fields(parsed_dict)

    # Output the result
    print("Extracted Data:")
    print(json.dumps(extracted_data, indent=4))

    # Optional: Store the extracted data in a Python variable
    attributes = extracted_data

    # Print the attributes
    print("Attributes Dictionary:")
    print(attributes)


    # Convert attributes to JSON string
    attributes_json = json.dumps(attributes)


    ret= client1.publish("v1/devices/me/attributes",attributes_json)             #topic-v1/devices/me/telemetry
    print("Please check LATEST ATTRIBUTE field of your device")
    print(attributes_json)
    
    print("\n")
    print("\n")


def deviceInfo(response):

    print(response)
    
    json_output_raw = parse_and_convert_to_json(response)
    print(json_output_raw)


    #Step 1: Parse the XML string into a dictionary
    parsed_dict = parse_xml_to_dict(response)

    #Step 2: Extract key fields from the dictionary (automated for unknown structure)
    extracted_data = extract_fields(parsed_dict)

    print(extracted_data)

    #Output the result
    print("Extracted Data:")
    print(json.dumps(extracted_data, indent=4))


    # Optional: Store the extracted data in a Python variable
    attributes = extracted_data

    # Print the attributes
    print("Attributes Dictionary:")
    print(attributes)

    # Convert attributes to JSON string
    attributes_json = json.dumps(attributes)

    data = attributes

    #print(device_data)

    #print("Device Name:", device_data['deviceName'])

    # Access individual elements
    device_name = data['deviceName']
    hardware_version = data['hardwareVersion']
    mac_address = data['macAddress']
    serial_number = data['serialNumber']
    telecontrol_id = data['telecontrolID']
    encoder_version = data['encoderVersion']
    version = data['version']
 
    device_type = data['deviceType']
    device_id = data['deviceID']
    firmware_released_date = data['firmwareReleasedDate']
    model = data['model']
    manufacturer = data['manufacturer']
    encoder_released_date = data['encoderReleasedDate']
    firmware_version = data['firmwareVersion']

    # Print individual values
    print("Device Name:", device_name)
    print("Hardware Version:", hardware_version)
    print("MAC Address:", mac_address)
    print("Serial Number:", serial_number)
    print("Telecontrol ID:", telecontrol_id)
    print("Encoder Version:", encoder_version)
    print("Version:", version)
    print("Device Type:", device_type)
    print("Device ID:", device_id)
    print("Firmware Released Date:", firmware_released_date)
    print("Model:", model)
    print("Manufacturer:", manufacturer)
    print("Encoder Released Date:", encoder_released_date)
    print("Firmware Version:", firmware_version)


    payload = "{"
    payload += "\"Hikvision_NVR_deviceName\":\"" + str(data["deviceName"]) + "\","
    payload += "\"Hikvision_NVR_deviceID\":\"" + str(data["deviceID"]) + "\","
    payload += "\"Hikvision_NVR_model\":\"" + str(data["model"]) + "\","

    payload += "\"Hikvision_NVR_serialNumber\":\"" + str(data["serialNumber"]) + "\","
    payload += "\"Hikvision_NVR_macAddress\":\"" + str(data["macAddress"]) + "\","
    payload += "\"Hikvision_NVR_firmwareVersion\":\"" + str(data["firmwareVersion"]) + "\","

    payload += "\"Hikvision_NVR_deviceType\":\"" + str(data["deviceType"]) + "\","
    payload += "\"Hikvision_NVR_Processor\":\"" + str("NA") + "\","
    payload += "\"Hikvision_NVR_hardwareVersion\":\"" + str(data["hardwareVersion"]) + "\","

    payload += "\"Hikvision_NVR_Manufacturer\":\"" + str(data["manufacturer"]) + "\""
    payload += "}"

    attributes_json = payload

    #ret= client1.publish("v1/devices/me/telemetry",attributes_json)             #topic-v1/devices/me/telemetry
    #ret= client1.publish("v1/devices/me/attributes",attributes_json)             #topic-v1/devices/me/telemetry
    if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1:
        insert_json_to_db(attributes_json)
    print("Please check LATEST ATTRIBUTE field of your device")
    print(attributes_json)
    
    print("\n")


def nvrPortIPAddress(response):

    print(response)
    
    json_output_raw = parse_and_convert_to_json(response)
    print(json_output_raw)


    #Step 1: Parse the XML string into a dictionary
    parsed_dict = parse_xml_to_dict(response)

    #Step 2: Extract key fields from the dictionary (automated for unknown structure)
    extracted_data = extract_fields(parsed_dict)

    print(extracted_data)

    #Output the result
    print("Extracted Data:")
    print(json.dumps(extracted_data, indent=4))


    # Optional: Store the extracted data in a Python variable
    attributes = extracted_data

    # Print the attributes
    print("Attributes Dictionary:")
    print(attributes)

    # Convert attributes to JSON string
    attributes_json = json.dumps(attributes)

    data = attributes

    # Access individual elements
    user_name = data['userName']
    output_state = data['outputState']
    pulse_duration = data['pulseDuration']
    ip_address = data['ipAddress']
    proxy_protocol = data['proxyProtocol']
    manage_port_no = data['managePortNo']

    # Print the values
    print("User Name:", user_name)
    print("Output State:", output_state)
    print("Pulse Duration:", pulse_duration)
    print("IP Address:", ip_address)
    print("Proxy Protocol:", proxy_protocol)
    print("Manage Port No:", manage_port_no)

    payload = "{"
    payload += "\"Hikvision_NVR_IPAddress\":\"" + str(ip_address) + "\","
    payload += "\"Hikvision_NVR_UserName\":\"" + str(user_name) + "\","
    payload += "\"Hikvision_NVR_ManagePortNo\":\"" + str(manage_port_no) + "\""
    payload += "}"

    attributes_json = payload

    #ret= client1.publish("v1/devices/me/telemetry",attributes_json)             #topic-v1/devices/me/telemetry
    #ret= client1.publish("v1/devices/me/attributes",attributes_json)             #topic-v1/devices/me/telemetry
    if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1:     
        insert_json_to_db(attributes_json)
    print("Please check LATEST ATTRIBUTE field of your device")
    print(attributes_json)
    
    print("\n")


def hDDInfo(response):

    print(response)
    
    #json_output_raw = parse_and_convert_to_json(response)
    json_output_raw = parse_and_convert_to_json_hdd(response)
    print("json_output_raw:")
    print(json_output_raw)

    # Parse the JSON string
    parsed_data = json.loads(json_output_raw)

    # Extracting the version
    version = parsed_data['hddList']['version']

    # Extract HDD information dynamically
    hdds = parsed_data['hddList'].get('hdds', [])
    max_slots = 4
    slot_mapping = {}

    # Create slot mapping for available HDDs
    available_hdds = []
    for i, hdd in enumerate(hdds):
        available_hdds.append({
            'id': hdd.get('id', str(i + 1)),
            'status': hdd.get('status', 'notexist'),
            'freeSpace': hdd.get('freeSpace', 0),
            'capacity': hdd.get('capacity', 0),
            'hddName': hdd.get('hddName', 'Unknown'),
            'hddPath': hdd.get('hddPath', 'Unknown'),
            'property': hdd.get('property', 'Unknown'),
            'hddType': hdd.get('hddType', 'Unknown')
        })

    # Map available HDDs to slots
    for i, hdd in enumerate(available_hdds):
        slot_mapping[i] = hdd['id']

    # Build payload dynamically
    payload = "{"
    for slot, hdd in enumerate(available_hdds):
        payload += "\"Hikvision_NVR_NoOfHDDSlots{}\":\"{}\",".format(slot + 1, hdd['id'])
        payload += "\"Hikvision_NVR_Status{}\":\"{}\",".format(slot + 1, hdd['status'])
        payload += "\"Hikvision_NVR_capacity{}\":\"{}\",".format(slot + 1, hdd['capacity'])
        payload += "\"Hikvision_NVR_freeSpace{}\":\"{}\",".format(slot + 1, hdd['freeSpace'])

    # Remove trailing comma and close JSON object
    if payload.endswith(","):
        payload = payload[:-1]
    payload += "}"

    # Payload
    print(payload)

    # Print results
#    print("Version: {}".format(version))
#    print("Slot Mapping: {}".format(slot_mapping))
#    print("Payload: {}".format(payload))

    # Wrap in a parent dictionary under "deviceAllInfo"
    #HDDInfo = {
    #    "Hikvision_NVR_HDDInfo": payload
    #}

    # Wrap the payload in "Hikvision_NVR_HDDInfo"
    hdd_info = "{\"Hikvision_NVR_HDDInfo\":" + payload + "}"

    # Convert to JSON string (optional)
    #json_HDDInfo = json.dumps(HDDInfo)    

    #attributes_json = payload

    attributes_json = hdd_info

    #ret= client1.publish("v1/devices/me/telemetry",attributes_json)             #topic-v1/devices/me/telemetry
    #ret= client1.publish("v1/devices/me/attributes",attributes_json)             #topic-v1/devices/me/telemetry
    if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1:     
        insert_json_to_db(attributes_json)
    print("Please check LATEST ATTRIBUTE field of your device")
    print(attributes_json)
    
    print("\n")


def dataTime(response):

    from datetime import datetime

    print(response)
    
    json_output_raw = parse_and_convert_to_json(response)
    print(json_output_raw)


    #Step 1: Parse the XML string into a dictionary
    parsed_dict = parse_xml_to_dict(response)

    #Step 2: Extract key fields from the dictionary (automated for unknown structure)
    extracted_data = extract_fields(parsed_dict)

    print(extracted_data)

    #Output the result
    print("Extracted Data:")
    print(json.dumps(extracted_data, indent=4))


    # Optional: Store the extracted data in a Python variable
    attributes = extracted_data

    # Print the attributes
    print("Telemetry Dictionary:")
    print(attributes)

    # Convert attributes to JSON string
    attributes_json = json.dumps(attributes)

    data = attributes


    # Get the localTime value
    local_time_str = data['localTime']

    # Parse the localTime string into a datetime object
    local_time_obj = datetime.strptime(local_time_str[:19], "%Y-%m-%dT%H:%M:%S")

    # Store date and time separately
    date_part = local_time_obj.date()  # Get the date part
    time_part = local_time_obj.time()  # Get the time part

    # Print the separated date and time
    print("Date:", date_part)
    print("Time:", time_part)


    payload = "{"
    payload += "\"Hikvision_NVR_Date\":\"" + str(date_part) + "\","
    payload += "\"Hikvision_NVR_Time\":\"" + str(time_part) + "\""
    payload += "}"

    attributes_json = payload

    #ret= client1.publish("v1/devices/me/telemetry",attributes_json)             #topic-v1/devices/me/telemetry
    if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1:     
        insert_json_to_db(attributes_json)
    print("Please check LATEST TELEMETRY field of your device")
    print(attributes_json)
    
    print("\n")


def cameraInfo_t(response):
    import xml.etree.ElementTree as ET
    import json
    import requests

    # URL of the API or service providing the XML response
    url = 'https://example.com/api/input_proxy_channels'  # Replace with the actual URL

    # Send a request to get the XML response
    response = requests.get(response)

    # Ensure the response is successful
    if response.status_code == 200:
        # Parse the XML content from the response
        xml_content = response.content
        root = ET.fromstring(xml_content)

        # Define the namespace used in the XML
        namespace = {'ns': 'http://www.hikvision.com/ver20/XMLSchema'}

        # Extract channel information
        channels = []

        for channel in root.findall('ns:InputProxyChannel', namespace):
            channel_info = {
                'id': channel.find('ns:id', namespace).text,
                'name': channel.find('ns:name', namespace).text,
                'protocol': channel.find('ns:sourceInputPortDescriptor/ns:proxyProtocol', namespace).text,
                'ip_address': channel.find('ns:sourceInputPortDescriptor/ns:ipAddress', namespace).text,
                'manage_port': channel.find('ns:sourceInputPortDescriptor/ns:managePortNo', namespace).text,
                'username': channel.find('ns:sourceInputPortDescriptor/ns:userName', namespace).text,
                'stream_type': channel.find('ns:sourceInputPortDescriptor/ns:streamType', namespace).text,
                'model': channel.find('ns:sourceInputPortDescriptor/ns:model', namespace).text if channel.find('ns:sourceInputPortDescriptor/ns:model', namespace) is not None else '',
                'serial_number': channel.find('ns:sourceInputPortDescriptor/ns:serialNumber', namespace).text if channel.find('ns:sourceInputPortDescriptor/ns:serialNumber', namespace) is not None else '',
                'firmware_version': channel.find('ns:sourceInputPortDescriptor/ns:firmwareVersion', namespace).text if channel.find('ns:sourceInputPortDescriptor/ns:firmwareVersion', namespace) is not None else '',
                'enable_anr': channel.find('ns:enableAnr', namespace).text if channel.find('ns:enableAnr', namespace) is not None else '',
                'enable_timing': channel.find('ns:enableTiming', namespace).text if channel.find('ns:enableTiming', namespace) is not None else '',
                'device_index': channel.find('ns:devIndex', namespace).text if channel.find('ns:devIndex', namespace) is not None else '',
                'two_way_audio_channel': channel.find('ns:twoWayAudioChannelIDList/ns:twoWayAudioChannelID', namespace).text if channel.find('ns:twoWayAudioChannelIDList/ns:twoWayAudioChannelID', namespace) is not None else '',
            }
            channels.append(channel_info)

        # Save the extracted information in JSON format
        json_output = json.dumps(channels, indent=4)

        # Print the JSON output
        print(json_output)

        # Optionally save the JSON to a file
        with open('channels_info.json', 'w') as json_file:
            json_file.write(json_output)

    else:
        #print(f"Failed to retrieve XML data. Status code: {response.status_code}")
        print("Failed to retrieve XML data. Status code:", {response.status_code})



import xml.etree.ElementTree as ET
import re
import json

def parse_xml_to_json_t(xml_string):
    # Function to strip namespace from tag
    def strip_namespace(tag):
        return re.sub(r'\{.*?\}', '', tag)

    # Recursive function to convert an XML element into a dictionary
    def xml_to_dict(element):
        data_dict = {}
        
        # If element has attributes, add them
        if element.attrib:
            data_dict['attributes'] = element.attrib

        # If element has children, recurse
        if list(element):
            # Check if the same tag appears multiple times, if so, store as a list
            data_dict['data'] = {}
            for child in element:
                tag = strip_namespace(child.tag)
                if tag not in data_dict['data']:
                    # If this tag appears for the first time
                    data_dict['data'][tag] = xml_to_dict(child)
                else:
                    # If this tag appears multiple times, convert to a list
                    if not isinstance(data_dict['data'][tag], list):
                        data_dict['data'][tag] = [data_dict['data'][tag]]  # Convert to list if it's not already
                    data_dict['data'][tag].append(xml_to_dict(child))
        else:
            # If element has no children, just add its text value
            data_dict = element.text or ""
        
        return data_dict

    try:
        # Parse the XML string
        root = ET.fromstring(xml_string)
        
        # Convert the XML tree to a dictionary
        xml_dict = {strip_namespace(root.tag): xml_to_dict(root)}
        
        # Convert the dictionary to JSON format
        json_data = json.dumps(xml_dict, indent=4)
        
        return json_data

    except ET.ParseError as e:
        print("Error parsing XML:", e)
        return None


def cameraInfo(response):

    json_output = parse_xml_to_json_t(response)
    print(json_output)

    # Parse the JSON string
    data = json.loads(json_output)

    input_proxy_channels = data['InputProxyChannelList']['data']['InputProxyChannel']
            
    channel_details = {}

    for channel in input_proxy_channels:
        channel_id = channel['data']['id']
        channel_details[channel_id] = {
            'Channel Name': channel['data']['name'],
            'Device Index': channel['data'].get('devIndex', 'N/A'),
            'IP Address': channel['data']['sourceInputPortDescriptor']['data']['ipAddress'],
            'Proxy Protocol': channel['data']['sourceInputPortDescriptor']['data']['proxyProtocol']
        }

    cam = Client('http://'+ipaddress, userid, passowrd)
    # Fetch and parse StreamingChannelList data
    response = cam.Streaming.channels(method='get', present='text')
    print(response)

    json_output = parse_xml_to_json_t(response)
    print(json_output)

    # Parse the JSON string
    data = json.loads(json_output)


    # List of specific channel IDs to process
    valid_channel_ids = ['101', '201', '301', '401', '501', '601', '701', '801', '901', '1001', '1101', '1201', '1301', '1401', '1501', '1601']


    streaming_channels = data['StreamingChannelList']['data']['StreamingChannel']

    for channel in streaming_channels:
        channel_id = channel['data']['id']
    
        # Check if the channel ID is in the valid_channel_ids list before processing
        if channel_id in valid_channel_ids:
            channel_key = str((int(channel_id) - 1) // 100)
        
            # Ensure the channel_key exists in channel_details before updating
            if channel_key in channel_details:
                channel_details[channel_key].update({
                    'Streaming Channel Name': channel['data']['channelName'],
                    'Video Resolution': "{}x{}".format(
                        channel['data']['Video']['data']['videoResolutionWidth'],
                        channel['data']['Video']['data']['videoResolutionHeight']
                    ),
                    'Max Frame Rate': channel['data']['Video']['data']['maxFrameRate'],
                })

            '''
            streaming_channels = data['StreamingChannelList']['data']['StreamingChannel']

            for channel in streaming_channels:
                channel_id = channel['data']['id']
                # Check if the channel ID exists, then add streaming details
                channel_id = str( ( ( int(channel_id)  - 1 ) / 100 ) )
                
                #print(channel_details)
                if channel_id in channel_details:
                    channel_details[channel_id].update({
                        'Streaming Channel Name': channel['data']['channelName'],
                        'Video Resolution': "{}x{}".format(
                            channel['data']['Video']['data']['videoResolutionWidth'],
                            channel['data']['Video']['data']['videoResolutionHeight']
                        ),
                        'Max Frame Rate': channel['data']['Video']['data']['maxFrameRate']
                    })

            '''                    

    # Combine everything under "cameraInfo"
    camera_info = {
        "Hikvision_NVR_cameraInfo": channel_details
        }

    print(camera_info)

    # Convert channel details to a JSON string
    channel_details_json = json.dumps(camera_info)
            
    # Output the JSON string
    print "Channel details JSON:", channel_details_json

    # Now you can use channel_details_json to send to another API
    attributes_json = channel_details_json
    if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1: 
        insert_json_to_db(attributes_json)
    print("Please check LATEST ATTRIBUTE field of your device")
    print(attributes_json)
    
    print("\n")


def initExternalDevice():
    
    print(" Initialise Devices ")

    # Sleep briefly to reduce CPU usage
    time.sleep(30.0)

    
    def sendParameters():

        def checkHBRT(): 
        
            # Initialize the camera client
            try:
                cam = Client('http://'+ipaddress, userid, passowrd)


                Heartbeat_t = "hikvision_nvr_on"

                payload = "{"
                payload += "\"Hikvision_NVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                payload += "}"

                # Now you can use channel_details_json to send to another API
                attributes_json = payload
                if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1:         
                    insert_json_to_db(attributes_json)
                print("Please check LATEST ATTRIBUTE field of your device")
                print(attributes_json)

            except ConnectionError as e:
                print("Failed to connect to the device at IP:", ipaddress)
                print("Error details:", e)
                # Optionally, you can add retry logic or log this error for further inspection.

                Heartbeat_t = "hikvision_nvr_off"

                payload = "{"
                payload += "\"Hikvision_NVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                payload += "}"

                # Now you can use channel_details_json to send to another API
                attributes_json = payload
                if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1:         
                    insert_json_to_db(attributes_json)
                print("Please check LATEST ATTRIBUTE field of your device")
                print(attributes_json)

            except Exception as e:
                print("Error while initializing the camera client:", e)

                Heartbeat_t = "hikvision_nvr_off"

                payload = "{"
                payload += "\"Hikvision_NVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                payload += "}"

                # Now you can use channel_details_json to send to another API
                attributes_json = payload
                if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1: 
                    insert_json_to_db(attributes_json)
                print("Please check LATEST ATTRIBUTE field of your device")
                print(attributes_json)
                pass            

        
        def sendTime():
            
            time.sleep(30.0)        
            # Initialize the camera client
            try:
                cam = Client('http://'+ipaddress, userid, passowrd)
                response = cam.System.time(method='get', present='text')
                print(response)
                dataTime(response)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass
            except ConnectionError as e:
                print("Failed to connect to the device at IP:", ipaddress)
                print("Error details:", e)
                pass            

        checkHBRT()
        sendTime()

    sendParameters()




import requests
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET
#import device_parameters_module
from datetime import datetime, timedelta
#from buffer_manager import insert_json_to_db

def search_matches(trackID, maxResults, searchResultPostion, startTime, endTime):
    # Get device parameters from the module
    device_type = 'HikvisionNVR1'
    devices = device_parameters_module.get_device_parameters(device_type)
    ipaddress = devices[0][2]
    userid = devices[0][3]
    password = devices[0][4]

    # API URL and headers
    url = "http://{}/ISAPI/ContentMgmt/search".format(ipaddress)
    headers = {
        "Content-Type": "application/xml",
        "Connection": "Keep-Alive"
    }

    # Request payload template
    payload_template = """<?xml version="1.0" encoding="utf-8"?>
    <CMSearchDescription>
        <searchID>C77384AD-66A0-0001-E7C2-1151F04F90B0</searchID>
        <trackIDList>
            <trackID>{}</trackID>
        </trackIDList>
        <timeSpanList>
            <timeSpan>
                <startTime>{}</startTime>
                <endTime>{}</endTime>
            </timeSpan>
        </timeSpanList>
        <maxResults>{}</maxResults>
        <searchResultPostion>{}</searchResultPostion>
        <metadataList>
            <metadataDescriptor>//recordType.meta.std-cgi.com</metadataDescriptor>
        </metadataList>
    </CMSearchDescription>"""

    search_position = searchResultPostion
    response_status_strg = "MORE"
    global_match_counter = 0
    total_duration = timedelta()
    first_start_time = None
    last_end_time = None

    try:
        while response_status_strg == "MORE":
            # Update payload with current parameters
            payload = payload_template.format(trackID, startTime, endTime, maxResults, search_position)

            # Make the POST request
            response = requests.post(url, data=payload, headers=headers, auth=HTTPDigestAuth(userid, password))

            if response.status_code == 200:
                #print "Request succeeded. Response:"
                #print response.text

                # Parse the XML response
                try:
                    root = ET.fromstring(response.content)
                    namespace = {'ns': 'http://www.hikvision.com/ver20/XMLSchema'}

                    response_status = root.find('ns:responseStatus', namespace).text
                    response_status_strg = root.find('ns:responseStatusStrg', namespace).text
                    num_of_matches = root.find('ns:numOfMatches', namespace).text

                    #print "\nParsed Response:"
                    #print "Response Status:", response_status
                    #print "Response Status Message:", response_status_strg
                    #print "Number of Matches:", num_of_matches

                    # Handle case when no matches are found
                    if int(num_of_matches) == 0:
                        print "No matches found. Verify the search criteria."
                        break

                    # Iterate through matches
                    match_list = root.findall('ns:matchList/ns:searchMatchItem', namespace)
                    for match in match_list:
                        track_id = match.find('ns:trackID', namespace).text
                        start_time = match.find('ns:timeSpan/ns:startTime', namespace).text
                        end_time = match.find('ns:timeSpan/ns:endTime', namespace).text
                        playback_uri = match.find('ns:mediaSegmentDescriptor/ns:playbackURI', namespace).text

                        # Convert start and end times to datetime
                        start_dt = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%SZ")
                        end_dt = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%SZ")
                        match_duration = end_dt - start_dt
                        total_duration += match_duration

                        # Update first and last times
                        if first_start_time is None or start_dt < first_start_time:
                            first_start_time = start_dt
                        if last_end_time is None or end_dt > last_end_time:
                            last_end_time = end_dt

                        global_match_counter += 1

                        #print "\nMatch {}:".format(global_match_counter)
                        #print "Track ID:", track_id
                        #print "Start Time:", start_time
                        #print "End Time:", end_time
                        #print "Playback URI:", playback_uri

                    # Increment search position for the next batch
                    search_position += len(match_list)

                except ET.ParseError as e:
                    print "Error parsing XML response:", str(e)
                    break
            else:
                print "Request failed with status code:", response.status_code
                print "Response content:", response.text
                break


        # Consolidated output
        consolidated_output = {
            "trackID": trackID,
            "total_matches": global_match_counter,
            "first_start_time": first_start_time,
            "last_end_time": last_end_time,
            "total_duration": total_duration,
            "search_window_start": startTime,
            "search_window_end": endTime
        }

        # Consolidated output
        #print "\nConsolidated Output:"
        #print "Total Matches:", global_match_counter
        #print "First Start Date/Time:", first_start_time
        #print "Last End Date/Time:", last_end_time
        #print "Total Duration:", total_duration
        #print "Search Window Start:", startTime
        #print "Search Window End:", endTime

        return consolidated_output

    except requests.exceptions.RequestException as e:
        print "Error during the request:", str(e)

        return None


def process_output(output):
    if output:
        print "\nProcessing Output in Another Function:"
        print "Track ID:", output["trackID"]
        print "Total Matches:", output["total_matches"]
        print "Duration:", output["total_duration"]
        print "Search Window Start:", output["search_window_start"]
        print "Search Window End:", output["search_window_end"]

        # Return the processed output
        return {
            "trackID": output["trackID"],
            "total_matches": output["total_matches"],
            "total_duration": output["total_duration"],
            "search_window_start": output["search_window_start"],
            "search_window_end": output["search_window_end"]
        }
    return None


def getTrackIDInfo_old():

    # Define a global variable to store the output
    processed_data_trackID101 = None
    processed_data_trackID201 = None
    processed_data_trackID301 = None
    processed_data_trackID401 = None
    processed_data_trackID501 = None
    processed_data_trackID601 = None
    processed_data_trackID701 = None
    processed_data_trackID801 = None
    processed_data_trackID901 = None
    processed_data_trackID1001 = None
    processed_data_trackID1101 = None
    processed_data_trackID1201 = None
    processed_data_trackID1301 = None
    processed_data_trackID1401 = None
    processed_data_trackID1501 = None
    processed_data_trackID1601 = None

    # Calculate the search window
    start_date = datetime.utcnow()
    end_date = start_date - timedelta(days=90)  # Corrected: end_date is 90 days before start_date
    startTime_t = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    endTime_t = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(startTime_t)
    print(endTime_t)                            


    # Example Function Call
    output = search_matches(
        trackID=101,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID101 = process_output(output)

    # Example Function Call
    output = search_matches(
        trackID=201,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID201 = process_output(output)

    # Example Function Call
    output = search_matches(
        trackID=301,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID301 = process_output(output)

    # Example Function Call
    output = search_matches(
        trackID=401,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID401 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=501,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID501 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=601,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    
    processed_data_trackID601 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=701,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID701 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=801,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID801 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=901,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID901 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1001,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1001 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1101,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1101 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1201,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1201 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1301,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1301 = process_output(output)

    # Example Function Call
    output = search_matches(
        trackID=1401,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1401 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1501,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1501 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1601,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1601 = process_output(output)


    payload = "["

    payload = "{"
            
    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID101["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID101["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID101["total_duration"]) + "\","    
    payload += "\"start_time\": \"" + str(processed_data_trackID101["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID101["search_window_end"]) + "\""
    payload += "},"
    
    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID201["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID201["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID201["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID201["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID201["search_window_end"]) + "\""
    payload += "},"
           
    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID301["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID301["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID301["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID301["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID301["search_window_end"]) + "\""
    payload += "},"
    
    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID401["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID401["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID401["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID401["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID401["search_window_end"]) + "\""
    payload += "},"

    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID501["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID501["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID501["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID501["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID501["search_window_end"]) + "\""
    payload += "},"
    
    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID601["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID601["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID601["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID601["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID601["search_window_end"]) + "\""
    payload += "},"

    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID701["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID701["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID701["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID701["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID701["search_window_end"]) + "\""
    payload += "},"
    
    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID801["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID801["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID801["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID801["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID801["search_window_end"]) + "\""
    payload += "},"

    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID901["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID901["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID901["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID901["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID901["search_window_end"]) + "\""
    payload += "},"
    
    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID1001["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID1001["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID1001["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID1001["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID1001["search_window_end"]) + "\""
    payload += "},"

    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID1101["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID1101["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID1101["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID1101["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID1101["search_window_end"]) + "\""
    payload += "},"
    
    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID1201["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID1201["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID1201["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID1201["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID1201["search_window_end"]) + "\""
    payload += "},"

    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID1301["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID1301["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID1301["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID1301["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID1301["search_window_end"]) + "\""
    payload += "},"
    
    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID1401["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID1401["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID1401["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID1401["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID1401["search_window_end"]) + "\""
    payload += "},"

    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID1501["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID1501["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID1501["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID1501["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID1501["search_window_end"]) + "\""
    payload += "},"
    
    payload += "{"
    payload += "\"camera_id\": \"" + str(processed_data_trackID1601["trackID"]) + "\","
    payload += "\"matches_found\": \"" + str(processed_data_trackID1601["total_matches"]) + "\","
    payload += "\"total_duration\": \"" + str(processed_data_trackID1601["total_duration"]) + "\","        
    payload += "\"start_time\": \"" + str(processed_data_trackID1601["search_window_start"]) + "\","
    payload += "\"end_time\": \"" + str(processed_data_trackID1601["search_window_end"]) + "\""
    payload += "}"

    payload += "}"

    payload += "]"

    camera_info = "{\"Hikvision_NVR_CameraRecInfo\":" + payload +  "}"    

    #attributes_json = camera_info

    attributes_json = payload
    if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1: 
        insert_json_to_db(attributes_json)
    print("Please check LATEST TELEMETRY field of your device")
    print(attributes_json)


def getTrackIDInfo():

    # Define a global variable to store the output
    processed_data_trackID101 = None
    processed_data_trackID201 = None
    processed_data_trackID301 = None
    processed_data_trackID401 = None
    processed_data_trackID501 = None
    processed_data_trackID601 = None
    processed_data_trackID701 = None
    processed_data_trackID801 = None
    processed_data_trackID901 = None
    processed_data_trackID1001 = None
    processed_data_trackID1101 = None
    processed_data_trackID1201 = None
    processed_data_trackID1301 = None
    processed_data_trackID1401 = None
    processed_data_trackID1501 = None
    processed_data_trackID1601 = None

    # Calculate the search window
    start_date = datetime.utcnow()
    end_date = start_date - timedelta(days=90)  # Corrected: end_date is 90 days before start_date
    startTime_t = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    endTime_t = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(startTime_t)
    print(endTime_t)                            


    # Example Function Call
    output = search_matches(
        trackID=101,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID101 = process_output(output)

    # Example Function Call
    output = search_matches(
        trackID=201,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID201 = process_output(output)

    # Example Function Call
    output = search_matches(
        trackID=301,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID301 = process_output(output)

    # Example Function Call
    output = search_matches(
        trackID=401,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID401 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=501,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID501 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=601,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    
    processed_data_trackID601 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=701,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID701 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=801,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID801 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=901,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID901 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1001,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1001 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1101,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1101 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1201,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1201 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1301,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1301 = process_output(output)

    # Example Function Call
    output = search_matches(
        trackID=1401,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1401 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1501,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1501 = process_output(output)


    # Example Function Call
    output = search_matches(
        trackID=1601,
        maxResults=40,
        searchResultPostion=0,
        startTime=endTime_t,
        endTime=startTime_t
    )
    processed_data_trackID1601 = process_output(output)


    payload = [
        {
            "camera_id": str(processed_data_trackID101["trackID"]),
            "matches_found": str(processed_data_trackID101["total_matches"]),
            "total_duration": str(processed_data_trackID101["total_duration"]),
            "start_time": str(processed_data_trackID101["search_window_start"]),
            "end_time": str(processed_data_trackID101["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID201["trackID"]),
            "matches_found": str(processed_data_trackID201["total_matches"]),
            "total_duration": str(processed_data_trackID201["total_duration"]),
            "start_time": str(processed_data_trackID201["search_window_start"]),
            "end_time": str(processed_data_trackID201["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID301["trackID"]),
            "matches_found": str(processed_data_trackID301["total_matches"]),
            "total_duration": str(processed_data_trackID301["total_duration"]),
            "start_time": str(processed_data_trackID301["search_window_start"]),
            "end_time": str(processed_data_trackID301["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID401["trackID"]),
            "matches_found": str(processed_data_trackID401["total_matches"]),
            "total_duration": str(processed_data_trackID401["total_duration"]),
            "start_time": str(processed_data_trackID401["search_window_start"]),
            "end_time": str(processed_data_trackID401["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID501["trackID"]),
            "matches_found": str(processed_data_trackID501["total_matches"]),
            "total_duration": str(processed_data_trackID501["total_duration"]),
            "start_time": str(processed_data_trackID501["search_window_start"]),
            "end_time": str(processed_data_trackID501["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID601["trackID"]),
            "matches_found": str(processed_data_trackID601["total_matches"]),
            "total_duration": str(processed_data_trackID601["total_duration"]),
            "start_time": str(processed_data_trackID601["search_window_start"]),
            "end_time": str(processed_data_trackID601["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID701["trackID"]),
            "matches_found": str(processed_data_trackID701["total_matches"]),
            "total_duration": str(processed_data_trackID701["total_duration"]),
            "start_time": str(processed_data_trackID701["search_window_start"]),
            "end_time": str(processed_data_trackID701["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID801["trackID"]),
            "matches_found": str(processed_data_trackID801["total_matches"]),
            "total_duration": str(processed_data_trackID801["total_duration"]),
            "start_time": str(processed_data_trackID801["search_window_start"]),
            "end_time": str(processed_data_trackID801["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID901["trackID"]),
            "matches_found": str(processed_data_trackID901["total_matches"]),
            "total_duration": str(processed_data_trackID901["total_duration"]),
            "start_time": str(processed_data_trackID901["search_window_start"]),
            "end_time": str(processed_data_trackID901["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID1001["trackID"]),
            "matches_found": str(processed_data_trackID1001["total_matches"]),
            "total_duration": str(processed_data_trackID1001["total_duration"]),
            "start_time": str(processed_data_trackID1001["search_window_start"]),
            "end_time": str(processed_data_trackID1001["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID1101["trackID"]),
            "matches_found": str(processed_data_trackID1101["total_matches"]),
            "total_duration": str(processed_data_trackID1101["total_duration"]),
            "start_time": str(processed_data_trackID1101["search_window_start"]),
            "end_time": str(processed_data_trackID1101["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID1201["trackID"]),
            "matches_found": str(processed_data_trackID1201["total_matches"]),
            "total_duration": str(processed_data_trackID1201["total_duration"]),
            "start_time": str(processed_data_trackID1201["search_window_start"]),
            "end_time": str(processed_data_trackID1201["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID1301["trackID"]),
            "matches_found": str(processed_data_trackID1301["total_matches"]),
            "total_duration": str(processed_data_trackID1301["total_duration"]),
            "start_time": str(processed_data_trackID1301["search_window_start"]),
            "end_time": str(processed_data_trackID1301["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID1401["trackID"]),
            "matches_found": str(processed_data_trackID1401["total_matches"]),
            "total_duration": str(processed_data_trackID1401["total_duration"]),
            "start_time": str(processed_data_trackID1401["search_window_start"]),
            "end_time": str(processed_data_trackID1401["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID1501["trackID"]),
            "matches_found": str(processed_data_trackID1501["total_matches"]),
            "total_duration": str(processed_data_trackID1501["total_duration"]),
            "start_time": str(processed_data_trackID1501["search_window_start"]),
            "end_time": str(processed_data_trackID1501["search_window_end"])
        },
        {
            "camera_id": str(processed_data_trackID1601["trackID"]),
            "matches_found": str(processed_data_trackID1601["total_matches"]),
            "total_duration": str(processed_data_trackID1601["total_duration"]),
            "start_time": str(processed_data_trackID1601["search_window_start"]),
            "end_time": str(processed_data_trackID1601["search_window_end"])
        }
    ]

    # Assuming 'payload' is the list of dictionaries you provided earlier
    camera_info = "{\"Hikvision_NVR_CameraRecInfo\":" + json.dumps(payload) + "}"

    attributes_json = camera_info
    if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1: 
        insert_json_to_db(attributes_json)
    print("Please check LATEST TELEMETRY field of your device")
    print(attributes_json)



import requests
from requests.auth import HTTPDigestAuth
import json
import re

# Define the function
def fetch_alert_stream_old(device_parameters_module, device_type):
    """
    Fetches the alert stream from a Hikvision NVR and extracts event details.

    Args:
        device_parameters_module: Module providing device parameters.
        device_type (str): The type of the device to fetch parameters for.

    Returns:
        dict: Extracted event data if an event is received, None otherwise.
    """
    # Get device parameters
    devices = device_parameters_module.get_device_parameters(device_type)
    ipaddress = devices[0][2]
    userid = devices[0][3]
    password = devices[0][4]

    # Define the URL for alertStream
    url = "http://{}/ISAPI/Event/notification/alertStream".format(ipaddress)

    # Regular expressions to extract the required fields
    fields_regex = {
        "channelID": re.compile(r"<channelID>(.*?)</channelID>"),
        "dateTime": re.compile(r"<dateTime>(.*?)</dateTime>"),
        "activePostCount": re.compile(r"<activePostCount>(.*?)</activePostCount>"),
        "eventType": re.compile(r"<eventType>(.*?)</eventType>"),
        "eventState": re.compile(r"<eventState>(.*?)</eventState>"),
        "dynChannelID": re.compile(r"<dynChannelID>(.*?)</dynChannelID>"),
        "eventDescription": re.compile(r"<eventDescription>(.*?)</eventDescription>")
    }

    try:
        # Use Digest Authentication for Hikvision devices
        response = requests.get(url, auth=HTTPDigestAuth(userid, password), stream=True)

        # Check if the response is successful
        if response.status_code == 200:
            buffer = ""  # Buffer to store the response lines
            for line in response.iter_lines():
                if line:  # Filter out keep-alive new lines
                    buffer += line.decode('utf-8') + "\n"

                    # Check if the buffer contains the closing tag for an event notification
                    if "</EventNotificationAlert>" in buffer:
                        # Extract the fields from the buffered data
                        extracted_data = {}
                        for key, regex in fields_regex.items():
                            match = regex.search(buffer)
                            if match:
                                extracted_data[key] = match.group(1)

                        # Clear the buffer for the next event
                        buffer = ""

                        # If extracted data contains an event type, return the data
                        if "eventType" in extracted_data:
                            yield extracted_data
        else:
            yield {
                "message": "Failed to connect.",
                "http_status": response.status_code,
                "response_text": response.text
            }

    except requests.exceptions.RequestException as e:
        yield {
            "message": "Error connecting to the device.",
            "error": str(e)
        }



import requests
from requests.auth import HTTPDigestAuth
import re
import json

def fetch_alert_stream(device_parameters_module, device_type):
    """
    Fetches the alert stream from a Hikvision NVR and extracts event details.

    Args:
        device_parameters_module: Module providing device parameters.
        device_type (str): The type of the device to fetch parameters for.

    Yields:
        dict: Extracted event data if an event is received, or error messages otherwise.
    """
    # Get device parameters
    try:
        devices = device_parameters_module.get_device_parameters(device_type)
        if not devices or len(devices[0]) < 5:
            yield {"error": "Device parameters are incomplete or missing."}
            return

        ipaddress = devices[0][2]
        userid = devices[0][3]
        password = devices[0][4]

    except Exception as e:
        yield {"error": "Failed to fetch device parameters: {}".format(str(e))}
        return

    # Define the URL for alertStream
    url = "http://{}/ISAPI/Event/notification/alertStream".format(ipaddress)

    # Regular expressions to extract the required fields
    fields_regex = {
        "channelID": re.compile(r"<channelID>(.*?)</channelID>"),
        "dateTime": re.compile(r"<dateTime>(.*?)</dateTime>"),
        "activePostCount": re.compile(r"<activePostCount>(.*?)</activePostCount>"),
        "eventType": re.compile(r"<eventType>(.*?)</eventType>"),
        "eventState": re.compile(r"<eventState>(.*?)</eventState>"),
        "dynChannelID": re.compile(r"<dynChannelID>(.*?)</dynChannelID>"),
        "eventDescription": re.compile(r"<eventDescription>(.*?)</eventDescription>"),
    }

    try:
        # Use Digest Authentication for Hikvision devices
        response = requests.get(
            url, auth=HTTPDigestAuth(userid, password), stream=True, timeout=10
        )

        # Check if the response is successful
        if response.status_code != 200:
            yield {
                "error": "Failed to connect to the NVR.",
                "http_status": response.status_code,
                "response_text": response.text,
            }
            return

        buffer = ""  # Buffer to store the response lines
        for line in response.iter_lines():
            if line:  # Filter out keep-alive new lines
                buffer += line.decode("utf-8") + "\n"

                # Check if the buffer contains the closing tag for an event notification
                if "</EventNotificationAlert>" in buffer:
                    # Extract the fields from the buffered data
                    extracted_data = {}
                    for key, regex in fields_regex.items():
                        match = regex.search(buffer)
                        if match:
                            extracted_data[key] = match.group(1)

                    # Clear the buffer for the next event
                    buffer = ""

                    # If extracted data contains an event type, yield the data
                    if "eventType" in extracted_data:
                        yield extracted_data

    except requests.exceptions.ConnectionError:
        yield {"error": "Connection to the NVR failed. Please check the network or IP address."}
    except requests.exceptions.Timeout:
        yield {"error": "Connection to the NVR timed out. Please verify device availability."}
    except requests.exceptions.RequestException as e:
        yield {"error": "Unexpected error occurred: {}".format(str(e))}


import time
import json
from datetime import datetime, timedelta


# *** Inactive Event Timeout Duration ***
#The timeout duration for transitioning a fault condition to an inactive state is defined in the variable event_timeout.
#In the provided code, this is configured as: event_timeout = timedelta(seconds=60)
#This means an inactive event will be sent 60 seconds after the last active event is received if no further updates occur for that event type and channel combination.
#If you need to change this duration: Simply modify the event_timeout value. For example, for a 5-minute timeout: event_timeout = timedelta(minutes=5)
#Summary
#Inactive Timeout: The duration after which an inactive response is sent is 60 seconds (configurable).
#Behavior: The timeout is reset only if new updates for the same fault condition are not received within this period.


# Log type mapping based on event type and state
log_type_mapping = {
    "videoloss": {
        "active": "camera_disconnect",
        "inactive": "camera_connection_established"
    },
    "shelteralarm": {
        "active": "camera_tampered",
        "inactive": "camera_tampered_restored"
    },
    "diskerror": {
        "active": "hdd_error",
        "inactive": "hdd_error_restored"
    }
}




# Global configuration
event_timeout = timedelta(seconds=60)  # Timeout period for event activity
events_received = {}  # Dictionary to track events and their timestamps
valid_event_types = ["videoloss", "shelteralarm", "diskerror"]

def process_event_response_new(event_type, channel_id, event_state, active_post_count="0"):
    """Generate a structured event response."""
    current_datetime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    response = {
        "eventDescription": "{} alarm".format(event_type),
        "eventType": event_type,
        "channelID": channel_id if channel_id else "N/A",
        "activePostCount": active_post_count,
        "dateTime": current_datetime,
        "eventState": event_state
    }
    return response

def process_event_response(event_type, event_state, date, time, channel_id):
    """Generate a structured event response."""
    log_type = log_type_mapping.get(event_type, {}).get(event_state, "unknown")

    response = {
        "branch": None,
        "log_type": log_type,
        "date": date,
        "time": time,
        "zone_no": None,
        "channelID": channel_id  # Include channelID in the response
    }
    return response



#Persistent Fault:
#Events in the "active" state that continue to be received within the timeout window remain in the events_received dictionary and are not transitioned to "inactive".
#Transition to "inactive": Events are marked as "inactive" only if no updates (last_active) have been received for the timeout duration, ensuring accurate state representation.
#Simulation: The response is printed as JSON using print(json.dumps(response)), simulating the actual output behavior.

def handle_event_old(event):
    """Handle the received event and update its status."""
    global events_received

    event_type = event.get("eventType")
    event_state = event.get("eventState", "inactive")
    channel_id = event.get("channelID", event.get("dynChannelID", None))

    # Only process the required event types
    if event_type not in valid_event_types:
        return

    # Specific condition to ignore videoloss for channelID = "0"
    if event_type == "videoloss" and channel_id == "0":
        return

    # Create a unique key for this event
    event_key = (event_type, channel_id)
    current_datetime = datetime.now()
    formatted_date = current_datetime.strftime("%d%m%y")
    formatted_time = current_datetime.strftime("%H%M")

    # If the event is new or its state has changed
    if event_key not in events_received or events_received[event_key]["eventState"] != event_state:
        # Generate and print the response
        response = process_event_response(event_type, event_state, formatted_date, formatted_time, channel_id)
        #response = process_event_response(event_type, "inactive", formatted_date, formatted_time, 0)
        print(json.dumps(response))  # Simulate returning the response

        attributes_json = json.dumps(response)
        if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1:                 
            insert_json_to_db(attributes_json)
        print("Please check LATEST TELEMETRY field of your device")
        print(attributes_json)

        # Update the event record
        events_received[event_key] = {
            "eventState": event_state,
            "last_received": current_datetime,
            "last_active": current_datetime if event_state == "active" else None
        }
    else:
        # Update only the timestamp for persistent active events
        if event_state == "active":
            events_received[event_key]["last_received"] = current_datetime


def handle_event(event):
    """Handle the received event and update its status."""
    global events_received

    event_type = event.get("eventType")
    event_state = event.get("eventState", "inactive")
    active_post_count = event.get("activePostCount", "0")
    channel_id = event.get("channelID", event.get("dynChannelID", None))

    # Only process the required event types
    if event_type not in valid_event_types:
        return

    # Specific condition to ignore videoloss for channelID = "0"
    if event_type == "videoloss" and channel_id == "0":
        return

    event_key = (event_type, channel_id)
    current_datetime = datetime.now()
    formatted_date = current_datetime.strftime("%d%m%y")
    formatted_time = current_datetime.strftime("%H%M")

    if event_key in events_received:
        # Update timestamp for active event
        events_received[event_key] = datetime.now()
    else:
        # New event, mark as active or inactive
        events_received[event_key] = datetime.now()
        #response = process_event_response(event_type, channel_id, event_state, active_post_count)
        response = process_event_response(event_type, event_state, formatted_date, formatted_time, channel_id)
        print(json.dumps(response))  # Simulate returning the response

        attributes_json = json.dumps(response)
        if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1:         
            insert_json_to_db(attributes_json)
        print("Please check LATEST TELEMETRY field of your device")
        print(attributes_json)



def check_event_timeouts_old():
    """Check for events that have timed out and mark them inactive."""
    global events_received
    current_time = datetime.now()
    timed_out_events = []

    for event_key, event_data in events_received.items():
        last_received = event_data["last_received"]
        last_active = event_data["last_active"]
        event_type, channel_id = event_key

        # Check if the event was active and hasn't been resolved
        if event_data["eventState"] == "active" and current_time - last_received > event_timeout:
            # Persistent fault: Do not reset timeout
            continue

        # Check if the event should transition to inactive
        if event_data["eventState"] == "active" and last_active and current_time - last_active > event_timeout:
            # Transition to inactive
            formatted_date = current_time.strftime("%d%m%y")
            formatted_time = current_time.strftime("%H%M")
            #response = process_event_response(event_type, "inactive", formatted_date, formatted_time)
            response = process_event_response(event_type, "inactive", formatted_date, formatted_time, channel_id)
            print(json.dumps(response))  # Simulate returning the response
            
            attributes_json = json.dumps(response)
            if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1:                     
                insert_json_to_db(attributes_json)
            print("Please check LATEST TELEMETRY field of your device")
            print(attributes_json)

            timed_out_events.append(event_key)

    # Remove timed-out inactive events
    for event_key in timed_out_events:
        del events_received[event_key]


def check_event_timeouts():
    """Check for events that have timed out and mark them inactive."""
    global events_received
    current_time = datetime.now()
    timed_out_events = []

    for event_key, last_received_time in events_received.items():
        if current_time - last_received_time > event_timeout:
            # Event has timed out
            formatted_date = current_time.strftime("%d%m%y")
            formatted_time = current_time.strftime("%H%M")
            
            event_type, channel_id = event_key
            #response = process_event_response(event_type, channel_id, "inactive")
            response = process_event_response(event_type, "inactive", formatted_date, formatted_time, channel_id)
            print(json.dumps(response))  # Simulate returning the response

            attributes_json = json.dumps(response)
            if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1:             
                insert_json_to_db(attributes_json)
            print("Please check LATEST TELEMETRY field of your device")
            print(attributes_json)
            
            timed_out_events.append(event_key)
    
    # Remove timed-out events
    for event_key in timed_out_events:
        del events_received[event_key]


# Example usage
def event_notification_alertStream():     
    
    import device_parameters_module

    # Infinite loop
    while True:

        device_type = 'HikvisionNVR1'
        for response in fetch_alert_stream(device_parameters_module, device_type):
            print(json.dumps(response, indent=4))
            
            json_str = json.dumps(response, indent=4)
            event = json.loads(json_str)
            
            handle_event(event)

            # Periodically check for timeouts
            check_event_timeouts()
       
#import time

# Define custom intervals (in seconds) for each condition
#intervals = [7200, 7600, 8000, 8400, 8800, 9100, 600]  # Adjust these intervals as needed for each condition
#intervals = [350, 400, 450, 500, 550, 600, 300]  # Adjust these intervals as needed for each condition
#intervals = [90, 230, 270, 200, 150, 115, 60]  # Adjust these intervals as needed for each condition#

#intervals = [300, 350, 400, 450, 500, 550]  # Adjust these intervals as needed for each condition
intervals = [86400, 300, 600, 21600, 21600, 86400]  # Adjust these intervals as needed for each condition

# Initialize last execution timestamps for each condition
start_time = time.time()
last_run_times = [start_time for _ in intervals]

#if __name__ == '__main__':
def task_with_delay():
    """Task that runs with a delay of 1 second in a loop."""

    initExternalDevice()
    
    # Infinite loop
    while True:
        print("Task with delay: Executing...")
        # Get the current time
        current_time = time.time()

        # Condition 1
        if current_time - last_run_times[0] >= intervals[0]:
            print("Executing Condition 1")
            last_run_times[0] = current_time
            # Initialize the camera client
            try:
                cam = Client('http://'+ipaddress, userid, passowrd)
                # Send the request to the camera for HDD storage details
                response = cam.System.deviceInfo(method='get', present='text')            
                # Call the deviceInfo function to process the response
                deviceInfo(response)
                
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass
            except ConnectionError as e:
                print("Failed to connect to the device at IP:", ipaddress)
                print("Error details:", e)
                pass

        # Condition 2
        if current_time - last_run_times[1] >= intervals[1]:
            print("Executing Condition 1")
            last_run_times[1] = current_time

            # Initialize the camera client
            try:
                cam = Client('http://'+ipaddress, userid, passowrd)

                Heartbeat_t = "hikvision_nvr_on"

                payload = "{"
                payload += "\"Hikvision_NVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                payload += "}"

                # Now you can use channel_details_json to send to another API
                attributes_json = payload
                if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1: 
                    insert_json_to_db(attributes_json)
                print("Please check LATEST ATTRIBUTE field of your device")
                print(attributes_json)

            except ConnectionError as e:
                print("Failed to connect to the device at IP:", ipaddress)
                print("Error details:", e)
                # Optionally, you can add retry logic or log this error for further inspection.

                Heartbeat_t = "hikvision_nvr_off"

                payload = "{"
                payload += "\"Hikvision_NVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                payload += "}"

                # Now you can use channel_details_json to send to another API
                attributes_json = payload
                if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1: 
                    insert_json_to_db(attributes_json)
                print("Please check LATEST ATTRIBUTE field of your device")
                print(attributes_json)

            except Exception as e:
                print("Error while initializing the camera client:", e)

                Heartbeat_t = "hikvision_nvr_off"

                payload = "{"
                payload += "\"Hikvision_NVR_Heartbeat\":\"" + str(Heartbeat_t) + "\""
                payload += "}"

                # Now you can use channel_details_json to send to another API
                attributes_json = payload
                if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1: 
                    insert_json_to_db(attributes_json)
                print("Please check LATEST ATTRIBUTE field of your device")
                print(attributes_json)
                pass            

        # Condition 3
        if current_time - last_run_times[2] >= intervals[2]:
            print("Executing Condition 3")
            last_run_times[2] = current_time

            # Initialize the camera client
            try:
                cam = Client('http://'+ipaddress, userid, passowrd)
                response = cam.System.time(method='get', present='text')
                print(response)
                dataTime(response)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass
            except ConnectionError as e:
                print("Failed to connect to the device at IP:", ipaddress)
                print("Error details:", e)
                pass            

        # Condition 4
        if current_time - last_run_times[3] >= intervals[3]:
            print("Executing Condition 4")
            last_run_times[3] = current_time

            # Initialize the camera client
            try:
                cam = Client('http://'+ipaddress, userid, passowrd)
                response = cam.ContentMgmt.Storage.hdd(method='get', present='text')
#                print(response)
                hDDInfo(response)
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass
            except ConnectionError as e:
                print("Failed to connect to the device at IP:", ipaddress)
                print("Error details:", e)
                pass
            
        # Condition 5
        if current_time - last_run_times[4] >= intervals[4]:
            print("Executing Condition 5")
            last_run_times[4] = current_time

            # Initialize the camera client
            try:
                cam = Client('http://'+ipaddress, userid, passowrd)
                # Fetch and parse InputProxyChannelList data
                response = cam.ContentMgmt.InputProxy.channels(method='get', present='text')
                print(response)
                cameraInfo(response)                
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass
            except ConnectionError as e:
                print("Failed to connect to the device at IP:", ipaddress)
                print("Error details:", e)
                pass
            

        # Condition 6
        if current_time - last_run_times[5] >= intervals[5]:
            print("Executing Condition 6")
            last_run_times[5] = current_time

            #nvrdvrstate = 10                                                                        
            # Initialize the camera client
            try:
                #cam = Client('http://'+ipaddress, userid, passowrd)
                getTrackIDInfo()
                
            except Exception as e:
                print("Error while initializing the camera client:", e)
                pass
            except ConnectionError as e:
                #print("Failed to connect to the device at IP:", ipaddress)
                print("Error details:", e)
                pass            

        # Sleep briefly to reduce CPU usage
        time.sleep(1.0)

#if __name__ == '__main__':
def task_without_delay():
    """Task that runs without any delay in a loop."""
    # Infinite loop
    while True:
        print("Task without delay: Executing...")
        #event_notification_alertStream()

        device_type = 'HikvisionNVR1'
            
        for response in fetch_alert_stream(device_parameters_module, device_type):
            if "error" in response:
                print("Error:", response["error"])
                continue  # Skip further processing for errors

            # Process the event
            print(json.dumps(response, indent=4))
            handle_event(response)
            check_event_timeouts()
            

import threading
import time

#def task_with_delay():
#    """Task that runs with a delay of 1 second in a loop."""
#    while True:
#        print("Task with delay: Executing...")
#        time.sleep(1)  # 1-second delay

#def task_without_delay():
#    """Task that runs without any delay in a loop."""
#    while True:
#        print("Task without delay: Executing...")

if __name__ == "__main__":
#def xThred():    
    # Create threads for each task
    thread_with_delay = threading.Thread(target=task_with_delay)
    thread_without_delay = threading.Thread(target=task_without_delay)

    # Set daemon to ensure threads close when the main program exits
    thread_with_delay.daemon = True
    thread_without_delay.daemon = True

    # Start the threads
    thread_with_delay.start()
    thread_without_delay.start()
    
    watchdog.reset()  # Reset watchdog after 10min
    
    # Keep the main thread alive to allow threads to run
    try:
        while True:
            time.sleep(0.1)  # Prevents main thread from consuming 100% CPU
    except KeyboardInterrupt:
        print("\nExiting program...")





        
