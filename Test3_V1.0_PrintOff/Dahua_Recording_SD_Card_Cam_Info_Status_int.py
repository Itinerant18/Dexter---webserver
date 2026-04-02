
import requests
from requests.auth import HTTPDigestAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import warnings
import json
import time  # Importing time module for delay
import re  # Importing regex for extracting object_id
import schedule  # Import schedule
from datetime import datetime, timedelta

import threading
import os
import sys

from requests.exceptions import ConnectionError  # Import ConnectionError
import xml.etree.ElementTree as ET

from buffer_manager import insert_json_to_db
 
import device_parameters_module
import logical_params_module


# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Initialize the database
logical_params_module.initialize_database()

#---------------------------- Watchdog Timer------------------------------------
class SoftwareWatchdog:
    def __init__(self, timeout=88200):
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
                    "Module Reboot": "Dahua SD, Cam Rec.",
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

  
# Initialize software watchdog with 88200-second timeout
watchdog = SoftwareWatchdog(timeout=88200)
#--------------------------------------------------------------------------------------

#---------------------------Getting Parameters from Database---------------------------
device_type = 'DahuaNVR1'
devices = device_parameters_module.get_device_parameters(device_type)

ipaddress = devices[0][2]
userid = devices[0][3]
password = devices[0][4]

print "IP Address: {}".format(ipaddress)
print "User Name: {}".format(userid)
print "Password: {}".format(password)
#--------------------------------------------------------------------------------------

def subsequent_processing(Dahua_NVR_CameraRecInfo):
    # Example: Process or save the log Dahua_NVR_CameraRecInfo
    attributes_json = json.dumps(Dahua_NVR_CameraRecInfo)
    if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:    
        insert_json_to_db(attributes_json)
    print("Please check LATEST TELEMETRY field of NVR Record Info")
    print(attributes_json)
#---------------------------------------------------------------------------------------------------------


#---------------------------- Getting Camera IP Address from Dahua NVR------------------------------------

# Function to fetch camera IP addresses from NVR
#def get_camera_ips_from_nvr():
def dahua_get_camera_ips_from_nvr():

    url = 'http://{}/cgi-bin/LogicDeviceManager.cgi?action=getCameraAll'.format(ipaddress)

    try:
        # Send request to fetch camera data
        response = requests.get(url,
                              auth=HTTPDigestAuth(userid, password),
                              verify=False)  # SSL verification disabled
        response.raise_for_status()      
        
        # Parse the response to extract camera IP addresses
        camera_ips = []

        # Split the response into lines and search for IP address lines
        for line in response.text.splitlines():
            if "DeviceInfo.Address=" in line:
                # Extract IP address using a regular expression
                match = re.search(r"DeviceInfo.Address=([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)", line)
                if match:
                    ip_address = match.group(1)  # Get the IP address
                    camera_ips.append(ip_address)
        
        if camera_ips:
#            print "[INFO] Extracted Camera IPs from Dahua NVR:", camera_ips
            device_parameters_module.update_camera_ips_by_type(device_type, camera_ips)
        else:
#            print "[WARN] No IPs found from NVR, trying to fetch from database..."
            camera_ips = device_parameters_module.get_camera_ips_by_type(device_type)

#        print "Extracted Camera IPs from Dahua NVR:", camera_ips
        #print "Extracted camera IPs:", camera_ips
        return camera_ips

    except requests.exceptions.RequestException as e:
        print "[ERROR] Could not fetch from NVR, loading from DB. Error:", e
        return device_parameters_module.get_camera_ips_by_type(device_type)
#-----------------------------------------------------------------------------------------------------------


#---------------------------- Getting SD Card Recording Info from Dahua Make Camera------------------------------------

# Function to extract SD card recording info for a specific camera
#def get_sd_card_recording_info(camera_ip):
def dahua_get_sd_card_recording_info(camera_ip):
    try:
        # Step 1: Call the first API to get the object value
        url1 = "http://{}/cgi-bin/mediaFileFind.cgi?action=factory.create".format(camera_ip)
        response1 = requests.get(url1, auth=HTTPDigestAuth(userid, password), verify=False)
        response1.raise_for_status()

        # Extract the object ID from the response
        object_id = response1.text.strip().split("=")[-1]

        # Get the current date and time for EndTime
        end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Set the StartTime (Fixed value)
        start_time_str = "2012-01-01 12:00:00"  # Fixed start time, could be dynamic if needed

        # Step 2: Call findFile API
        url2 = (
            "http://{}/cgi-bin/mediaFileFind.cgi?"
            "action=findFile&object={}"
            "&condition.Channel=1"
            "&condition.StartTime={}"
            "&condition.EndTime={}"
            "&condition.VideoStream=Main"
        ).format(camera_ip, object_id, start_time_str.replace(' ', '%20'), end_time_str.replace(' ', '%20'))

        requests.get(url2, auth=HTTPDigestAuth(userid, password), verify=False).raise_for_status()

        # Step 3: Call findNextFile API to get file details
        recorded_dates = set()
        while True:
            url3 = "http://{}/cgi-bin/mediaFileFind.cgi?action=findNextFile&object={}&count=100".format(camera_ip, object_id)
            response3 = requests.get(url3, auth=HTTPDigestAuth(userid, password), verify=False)
            response3.raise_for_status()
  
            lines = response3.text.splitlines()
            if not any("FilePath=" in line for line in lines):  # Stop if no more files
               break             
         
            # Extract recording dates
            for line in lines:
                if "FilePath=" in line:
                    date_part = line.split("=")[-1].split("/")[3]  # Extract YYYY-MM-DD
                    recorded_dates.add(date_part)
        
            total_recording_days = len(recorded_dates)
        
            # Format the start and end dates for the output
            start_date = min(recorded_dates) if recorded_dates else 'N/A'
            end_date = max(recorded_dates) if recorded_dates else 'N/A'
        
#        print "Total Recording Days for Camera {}: {}".format(camera_ip, len(recorded_dates))

        # Store the data for this camera in the result list in the requested format
        Dahua_SD_card_rec_info = {
            "camera_ip": camera_ip,
            "start_date": start_date,
            "end_date": end_date,
            "total_recording_days": total_recording_days
        }
        
        # Create a list with one element for this camera
        Dahua_SD_card_rec_info_list = {
            "Dahua_SD_card_rec_info": [
                Dahua_SD_card_rec_info
            ]
        }
        
        # Convert the dictionary to JSON
        attributes_json = json.dumps(Dahua_SD_card_rec_info_list)

        # Insert into the database (Buffer Manager)
        if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
            insert_json_to_db(attributes_json)  # Insert into the database

        # Print confirmation message
        #print "SD Card Record info sent to the database for camera:", camera_ip
#        print "Please check LATEST TELEMETRY field of SD Card Record Info"
#        print attributes_json
        
        return Dahua_SD_card_rec_info_list  # Return in the correct format

    except requests.exceptions.RequestException, e:  # Python 2 exception handling
        print "An error occurred while fetching recording info for camera {}: {}".format(camera_ip, e)
        return None



#def main_SDcard_Record_Info():
def dahua_main_SDcard_Record_Info():
    # Get camera IPs from NVR
    #camera_ips = get_camera_ips_from_nvr()
    camera_ips = dahua_get_camera_ips_from_nvr()
    if camera_ips:
        print("Camera IPs extracted:", camera_ips)
    else:
        print("No camera IPs found.")
        return

    # For each camera, extract SD card recording information
    all_recording_info = []
    for camera_ip in camera_ips:
        #recording_info = get_sd_card_recording_info(camera_ip)
        recording_info = dahua_get_sd_card_recording_info(camera_ip)
        if recording_info:
            all_recording_info.append(recording_info)
            
    else:
        print "No more SD card recording information to process..."
#---------------------------------------------------------------------------------------------------------

#---------------------------- Getting SD Card Recording Info from Hikvision Make Camera------------------------------------

# Function to extract SD card recording info for a specific camera
#def get_sd_card_recording_info(camera_ip):
def hik_get_sd_card_recording_info(camera_ip):
    try:
        current_utc_time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        url = "http://{}/ISAPI/ContentMgmt/search".format(camera_ip)
        search_result_position = 1
        recording_dates = set()  # Store unique recording dates
        MAX_RESULTS = 30  # Number of results per request
        first_recording_date = None  # To track the first recording date
        last_recording_date = None   # To track the last recording date

        for i in range(1, 17):
            track_id = 100 * i + 1
            first_recording_time = None

            while True:
                start_time = "2000-01-01T00:00:00Z" if first_recording_time is None else first_recording_time

                xml_body = """<?xml version="1.0" encoding="utf-8"?>
                <CMSearchDescription>
                    <searchID>88C2CD4D-D3FA-4AD4-BD80-555C18205DCC</searchID>
                    <trackList>
                        <trackID>{}</trackID>
                    </trackList>
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
                </CMSearchDescription>""".format(track_id, start_time, current_utc_time, MAX_RESULTS, search_result_position)

                headers = {"Content-Type": "application/xml"}
                
                try:
                    response = requests.post(url, auth=HTTPDigestAuth(userid, password), data=xml_body, headers=headers, verify=False, timeout=30)
                    response.raise_for_status()  # Raises an HTTPError for bad responses

                except requests.exceptions.Timeout:
#                    print("Timeout occurred while connecting to camera: {}".format(camera_ip))
                    return None
                except requests.exceptions.RequestException as e:
                    #print("Error during request to camera {}: {}".format(camera_ip, e))
                    return None

                # Check if the response is empty
                if not response.text.strip():
#                    print("Empty response received from camera: {}".format(camera_ip))
                    return None

                try:
                    # Parse XML
                    root = ET.fromstring(response.text)

                    # Check if there are more results
                    response_status_strg = root.find(".//{http://www.hikvision.com/ver20/XMLSchema}responseStatusStrg")
                    if response_status_strg is not None and response_status_strg.text != "MORE":
                        #print("All results fetched. Exiting loop.")
                        break  # Stop if no more results

                    # Extract unique recording dates
                    for item in root.findall(".//{http://www.hikvision.com/ver20/XMLSchema}searchMatchItem"):
                        start_time = item.find(".//{http://www.hikvision.com/ver20/XMLSchema}timeSpan/{http://www.hikvision.com/ver20/XMLSchema}startTime")
                        if start_time is not None:
                            recording_date = start_time.text[:10]  # Extract YYYY-MM-DD
                            recording_dates.add(recording_date)

                            # Update the first and last recording dates
                            recording_date_obj = datetime.strptime(recording_date, "%Y-%m-%d")
                            if first_recording_date is None or recording_date_obj < first_recording_date:
                                first_recording_date = recording_date_obj
                            if last_recording_date is None or recording_date_obj > last_recording_date:
                                last_recording_date = recording_date_obj

                    # Move to the next batch of results
                    search_result_position += MAX_RESULTS
                    time.sleep(1)  # Prevent API spam

                except ET.ParseError as e:
                    print "XML Parsing Error:", e
                    break

        # After collecting all the dates, calculate total recording days
        if first_recording_date and last_recording_date:
            continuous_days = (last_recording_date - first_recording_date).days + 1
        else:
            continuous_days = 0  # In case no recordings were found

        # Construct the Hik_SD_card_rec_info dictionary
        Hik_SD_card_rec_info = {
            "camera_ip": camera_ip,
            "start_date": first_recording_date.strftime("%Y-%m-%dT%H:%M:%SZ") if first_recording_date else None,
            "end_date": last_recording_date.strftime("%Y-%m-%dT%H:%M:%SZ") if last_recording_date else None,
            "total_recording_days": continuous_days
        }

        return Hik_SD_card_rec_info

    except requests.exceptions.RequestException as e:
       # print("Error fetching SD card recordings for {}: {}".format(camera_ip, e))
        return None




#def main_SDcard_Record_Info():
def hik_main_SDcard_Record_Info():
    #camera_ips = get_camera_ips_from_nvr()  # Fetch camera IPs from NVR
    camera_ips = dahua_get_camera_ips_from_nvr()  # Fetch camera IPs from NVR
    if camera_ips:
        print "Camera IPs extracted:", camera_ips
    else:
        print "No camera IPs found."
        return

    Hik_SD_card_rec_info_list = []  # Initialize the list to hold all camera SD card info

    for camera_ip in camera_ips:
        #recording_info = get_sd_card_recording_info(camera_ip)
        recording_info = hik_get_sd_card_recording_info(camera_ip)
        if recording_info:
            Hik_SD_card_rec_info_list.append(recording_info)
        else:
            # If the camera does not return any valid data, append a default entry
            Hik_SD_card_rec_info_list.append({
                "camera_ip": camera_ip,
                "total_recording_days": 0,
                "start_date": None,
                "end_date": None
            })
    
    # Prepare the final output in the desired format
    final_output = {
        "Hik_SD_card_rec_info_list": Hik_SD_card_rec_info_list
    }

    # Convert the result to a JSON string
    attributes_json = json.dumps(final_output)

    # Insert the JSON into the database (if necessary)
    if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
        insert_json_to_db(attributes_json)
#        print "SD Card Record info sent to database: {}".format(attributes_json)

#    print "Final SD Card Record Info: {}".format(attributes_json)
#---------------------------------------------------------------------------------------------------------



#----------------------------------------------------------------------------------------------------------
#---------------------------- Getting HDD Recording Info from Dahua NVR------------------------------------

# NVR info
base_url = 'https://{}/cgi-bin/mediaFileFind.cgi'.format(ipaddress)


session = requests.Session()
session.auth = HTTPDigestAuth(userid, password)
session.verify = False

start_time = '2010-01-01 00:00:00'
end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_object_id():
    try:
        res = session.get("{0}?action=factory.create".format(base_url), timeout=10)
        if res.ok:
            match = re.search(r'result=(\d+)', res.text)
            if match:
                return match.group(1)
    except:
        pass
    return None

def get_recording_days(channel, object_id):
    days = set()
    first_recording_date = None  # Initialize the variable for first recording date
    params_find = {
        'object': object_id,
        'condition.Channel': channel,
        'condition.Dirs[0]': '/mnt/dvr/sda0',
        'condition.Types[0]': 'dav',
        'condition.Events[0]': 'AlarmLocal',
        'condition.Events[1]': 'VideoMotion',
        'condition.StartTime': start_time,  # Old start time, will not be used now
        'condition.EndTime': end_time,
        'condition.VideoStream': 'Main'
    }

    try:
        res = session.get(base_url + "?action=findFile", params=params_find, timeout=10)
        if not res.ok:
            return days, first_recording_date
    except:
        return days, first_recording_date

    for _ in range(1000):
        try:
            next_res = session.get(base_url + "?action=findNextFile", params={"object": object_id, "count": 100}, timeout=10)
            if not next_res.ok:
                break
            new_days = set(re.findall(r'(\d{4}-\d{2}-\d{2})', next_res.text))
            if not new_days:
                break
            days.update(new_days)
            
            # Capture the first recording date from the first batch of new_days
            if not first_recording_date and new_days:
                first_recording_date = min(new_days)
        except:
            break

    return days, first_recording_date

    # Main execution
    total_all_channels = 0

    for ch in range(1, 17):
#        print("\nChecking Channel {0}...".format(ch))
        days = set()
        first_recording_date = None  # <-- ADD THIS LINE
        for attempt in range(5):
            object_id = get_object_id()
            if not object_id:
                time.sleep(1)
                continue

            days, first_recording_date = get_recording_days(ch, object_id)
            if days:
                break
            time.sleep(1)

        total = len(days)
        total_all_channels += total
#        print("Total Recording Days: {0}".format(total))
    
        # Print the start date, end date, and total recording days for this channel
#        print(" ")
#        print("Channel {}:".format(ch))
#        print(" Start Date: {}".format(first_recording_date if first_recording_date else start_time))
#        print(" End Date: {}".format(end_time))
#        print(" Total Recording Days: {}".format(total))
#        print(" ")

        # Store the data for this channel in the result list
        Dahua_recording_info = {
            "channel": ch,
            "start_date": first_recording_date if first_recording_date else start_time,  # Use first recording date or fallback to start_time
            "end_date": end_time,
            "total_recording_days": total
        }

#    print("\n Final Total Recording Days Across All Channels: {0}".format(total_all_channels))

def main_NVR_Record_Info():
    """
    Main function to process and send the NVR recording data.
    """
    # Create an empty list to store all the channel data
    Dahua_NVR_CameraRecInfo = {
        "Dahua_NVR_CameraRecInfo": []  # Change to Dahua_NVR_CameraRecInfo
    }

    # Get the channel data for all channels at once
    for ch in range(1, 17):
#        print("\nChecking Channel {0}...".format(ch))
        object_id = get_object_id()
        if object_id:
            days, first_recording_date = get_recording_days(ch, object_id)
            Dahua_recording_info = {
                "channel": ch,
                "start_date": first_recording_date if first_recording_date else start_time,  # Dynamically set start date
                "end_date": end_time,
                "total_recording_days": len(days)
            }
            if Dahua_recording_info["total_recording_days"] > 0:
                # Append this channel's data into the Dahua_NVR_CameraRecInfo dictionary
                Dahua_NVR_CameraRecInfo["Dahua_NVR_CameraRecInfo"].append(Dahua_recording_info)
        else:
            print("Failed to retrieve object_id for Channel {0}. Retrying...".format(ch))

    # Now that all channel data has been collected, send it to the database
    if Dahua_NVR_CameraRecInfo["Dahua_NVR_CameraRecInfo"]:
        subsequent_processing(Dahua_NVR_CameraRecInfo)
    else:
        print("No data to process.")
#---------------------------------------------------------------------------------------------------------


#------------------------------------ Getting SD Card Info from Dahua Make Camera------------------------------------

#def get_sd_card_info(camera_ip):
def dahua_get_sd_card_info(camera_ip):
    try:
        # First URL - Fetch SD card details
        sd_card_url = "http://{}/cgi-bin/storageDevice.cgi?action=getDeviceAllInfo".format(camera_ip)
        response_sd = requests.get(sd_card_url, auth=HTTPDigestAuth(userid, password), verify=False)
    
        # Check if the response_sd status is OK (200)
        response_sd.raise_for_status()

        # Manually parse the plain-text response_sd (not JSON)
        response_text = response_sd.text

        # Initialize a dictionary to store parsed SD card information
        parsed_info = {}

        # Split the response_sd into lines and process each line
        lines = response_text.splitlines()

        for line in lines:
            # Skip empty lines
            if not line.strip():
                continue

            # Split the line by '=' to extract key-value pairs
            key_value = line.split('=')
            if len(key_value) == 2:
                key = key_value[0].strip()
                value = key_value[1].strip()

                # Store the key-value pairs in the dictionary
                parsed_info[key] = value

        # Now, you can extract specific information from the parsed_info dictionary
        # For example, extracting TotalBytes and UsedBytes:
        total_bytes = float(parsed_info.get('list.info[0].Detail[0].TotalBytes', 0))
        used_bytes = float(parsed_info.get('list.info[0].Detail[0].UsedBytes', 0))

        # Second URL - Fetch device details
        device_info_url = "http://{}/cgi-bin/magicBox.cgi?action=getSystemInfoNew".format(camera_ip)
        response_device = requests.get(device_info_url, auth=HTTPDigestAuth(userid, password), verify=False)
    
        if response_device.status_code == 200:
            device_data = response_device.text.split("\n")
            device_type = serial_number = None

            for line in device_data:
                line = line.strip()  # Remove trailing \r and spaces
                if "deviceType=" in line:
                    device_type = line.split("=", 1)[1].strip()  # Explicitly strip any \r
                elif "serialNumber=" in line:
                    serial_number = line.split("=", 1)[1].strip()  # Explicitly strip any \r
        else:
#            print "Failed to get device info from Camera Info"
            return None

        # Merging data
        Dahua_SD_card_info = {
            "camera_ip": camera_ip,
            "TotalBytes": total_bytes,
            "UsedBytes": used_bytes,
            "deviceType": device_type,
            "serialNumber": serial_number
        }

        # Create a list with all SD card info entries for this camera
        Dahua_SD_card_info_list = {
            "Dahua_SD_card_info": [Dahua_SD_card_info]
        }

        # Insert into the database if active integration is enabled
        attributes_json = json.dumps(Dahua_SD_card_info_list)
        if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
            insert_json_to_db(attributes_json)

        # Print confirmation message
#        print "SD Card info sent to the database for camera:", camera_ip
#        print "Please check LATEST TELEMETRY field of SD Card Info"
#        print attributes_json

        return Dahua_SD_card_info_list  # Return the SD card info

    except requests.exceptions.RequestException, e:
#        print "An error occurred while fetching SD Card info for camera {}: {}".format(camera_ip, e)
        return None


#def main_SDcard_Info():
def dahua_main_SDcard_Info():
    # Get camera IPs from NVR
    #camera_ips = get_camera_ips_from_nvr()
    camera_ips = dahua_get_camera_ips_from_nvr()
    if camera_ips:
        print("Camera IPs extracted:", camera_ips)
    else:
        print("No camera IPs found.")
        return

    # For each camera, extract SD card recording information
    all_sd_card_info = []
    for camera_ip in camera_ips:
        sd_card_info = dahua_get_sd_card_info(camera_ip)
        if sd_card_info:
            all_sd_card_info.append(sd_card_info)
    
    # Handle the case where no SD card info was gathered
    if not all_sd_card_info:
#        print("No SD card info was found for any camera.")
        return

#---------------------------------------------------------------------------------------------------------

#------------------------------------ Getting SD Card Info from Hikvision Make Camera------------------------------------
#def get_sd_card_info(camera_ip):
def hik_get_sd_card_info(camera_ip):
    try:
        # First URL - Fetch SD card details
        sd_card_url = "http://{}/ISAPI/ContentMgmt/storage/hdd/capabilities".format(camera_ip)

        # Define the XML namespace
        namespaces = {"ns10": "http://www.hikvision.com/ver10/XMLSchema", "ns20": "http://www.hikvision.com/ver20/XMLSchema"}
        
        # Set to store unique HDD details
        hdd_info_list = []

        while True:
            # Send API request
            response = requests.get(
                sd_card_url,
                auth=HTTPDigestAuth(userid, password),
                headers={"Content-Type": "application/xml"},
                timeout=10
            )
        
#            print "Status Code: {}, Response Length: {}".format(response.status_code, len(response.text))
            
            if response.status_code != 200 or not response.text.strip():
#                print "Error: No valid response received. Stopping."
                break
                
            try:
                # Parse XML
                root = ET.fromstring(response.text)

                # Extract HDD information
                for hdd in root.findall(".//ns20:hdd", namespaces):
                    hdd_name = hdd.find("ns20:hddName", namespaces)
                    capacity = hdd.find("ns20:capacity", namespaces)
                    free_space = hdd.find("ns20:freeSpace", namespaces)
                    status = hdd.find("ns20:status", namespaces)

                    hdd_info = {
                        "HDD Name": hdd_name.text if hdd_name is not None else "Unknown",
                        "Capacity (MB)": capacity.text if capacity is not None else "Unknown",
                        "Free Space (MB)": free_space.text if free_space is not None else "Unknown",
                        "Status": status.text if status is not None else "Unknown",
                    }
                    
                    hdd_info_list.append(hdd_info)
                    
                break  # Exit after fetching HDD info
                
            except ET.ParseError as e:
                #print "XML Parsing Error: {}".format(e)
                break

            time.sleep(1)  # Prevent excessive API requests
        # Print results
#        print "\nHDD Storage Information:"
        if not hdd_info_list:
            print("No HDD info found.")
        else:     
            for hdd_info in hdd_info_list:
                print "HDD Name: {}".format(hdd_info['HDD Name'])
#                print "Capacity: {} MB".format(hdd_info['Capacity (MB)'])
#                print "Free Space: {} MB".format(hdd_info['Free Space (MB)'])
#                print "Status: {}".format(hdd_info['Status'])
#                print "=" * 40

        # Second URL - Fetch device details (camera device info)
        device_info_url = "http://{}/ISAPI/System/deviceInfo".format(camera_ip)
        response_device = requests.get(device_info_url, auth=HTTPDigestAuth(userid, password), verify=False)
        response_device.raise_for_status()  # Raises an HTTPError for bad responses
        
        # Check if the response_device status is OK (200)
        if response_device.status_code == 200:
            # Parse the XML response for device details
            root_device = ET.fromstring(response_device.text)

            # Extract required information from the device XML (with correct namespace 'ns20')
            model = root_device.find('.//ns20:model', namespaces=namespaces)
            serial_number = root_device.find('.//ns20:serialNumber', namespaces=namespaces)
            manufacturer = root_device.find('.//ns20:manufacturer', namespaces=namespaces)

            model = model.text if model is not None else None
            serial_number = serial_number.text if serial_number is not None else None
            manufacturer = manufacturer.text if manufacturer is not None else None
            
            # Construct the device info dictionary
            device_info = {
               "model": model,
               "serialNumber": serial_number,
               "manufacturer": manufacturer
            }

            # Ensure there is HDD info before merging
            if hdd_info_list:
                # Merging data
                Hik_SD_card_info = {
                    "camera_ip": camera_ip,
                    "TotalBytes": hdd_info_list[0].get('Capacity (MB)', 0),  # Use first HDD entry for capacity
                    "UsedBytes": hdd_info_list[0].get('Free Space (MB)', 0),  # Use first HDD entry for free space
                    "model": model,
                    "serialNumber": serial_number,
                    "manufacturer": manufacturer
                }

                # Create a list with all SD card info entries for this camera
                Hik_SD_card_info_list = {
                    "Hik_SD_card_info": [Hik_SD_card_info]
                }

                # Insert into the database if active integration is enabled
                attributes_json = json.dumps(Hik_SD_card_info_list)
                if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
                    insert_json_to_db(attributes_json)

                # Print confirmation message
               # print("SD Card info sent to the database for camera:", camera_ip)
               # print("Please check LATEST TELEMETRY field of SD Card Info")
#                print(attributes_json)

                return Hik_SD_card_info_list  # Return the SD card info

            else:
                print("No HDD information available to process.")
                return None
        
        else:
            print("Failed to get device info from Camera Info", camera_ip)
            return None
        
    except requests.exceptions.RequestException as e:
        print "An error occurred while fetching SD Card info for camera {}: {}".format(camera_ip, e)
        return None


#def main_SDcard_Info():
def hik_main_SDcard_Info():
    # Get camera IPs from NVR
    #camera_ips = get_camera_ips_from_nvr()
    camera_ips = dahua_get_camera_ips_from_nvr()  # Fetch camera IPs from NVR
    if camera_ips:
        print "Camera IPs extracted:", camera_ips
    else:
        print "No camera IPs found."
        return

    # For each camera, extract SD card recording information
    all_sd_card_info = []
    for camera_ip in camera_ips:
        #sd_card_info = get_sd_card_info(camera_ip)
        sd_card_info = hik_get_sd_card_info(camera_ip)
        if sd_card_info:
            all_sd_card_info.append(sd_card_info)
    
    # Handle the case where no SD card info was gathered
    if not all_sd_card_info:
        print "No SD card info was found for any camera."
        return  

#---------------------------------------------------------------------------------------------------------


#--------------------------------------------Dahua Make camera Status------------------------------------------ 

def get_dahua_cam_status(camera_ip):  
   
    sd_card_info_url = "http://{}/cgi-bin/global.cgi?action=getCurrentTime".format(camera_ip)

    try:       
        response_sd = requests.get(sd_card_info_url, auth=HTTPDigestAuth(userid, password), verify=False)
        response_sd.raise_for_status()

        if response_sd.status_code == 200:
            print("Dahua NVR Camera is active.")
        return "Active"

    except requests.exceptions.ConnectionError as e:
        print("Connection error to Dahua NVR at IP:", camera_ip, "Error:", e)
        return "Inactive"

    except Exception as e:
        print("Error initializing Dahua NVR:", e)
        return "Inactive"


def main_dahua_cam_status():
    # Get camera IPs from NVR
    #camera_ips = get_camera_ips_from_nvr()
    camera_ips = dahua_get_camera_ips_from_nvr()
    if camera_ips:
        print("Camera IPs extracted:", camera_ips)
    else:
        print("No camera IPs found.")
        return       
 
    # For each camera, extract camera status information
    dahua_camera_status = []
    
    for camera_ip in camera_ips:
        camera_status = get_dahua_cam_status(camera_ip)
        if camera_status == 'Active':
            dahua_camera_status.append({
                "camera_ip": camera_ip,
                "camera_status": 'Active'
            })
        else:
            dahua_camera_status.append({
                "camera_ip": camera_ip,
                "camera_status": None
            })
    # Prepare the final output in the desired format
    final_output = {
        "dahua_camera_status": dahua_camera_status
    }

    # Convert the result to a JSON string
    attributes_json = json.dumps(final_output)

    # Insert the JSON into the database (if necessary)
    if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
        insert_json_to_db(attributes_json)
#        print "Camera uptime status sent to database: {}".format(attributes_json)    

#    print "Final Camera uptime status Info: {}".format(attributes_json)
#---------------------------------------------------------------------------------------------------------

#------------------------------------------Hikvision Make camera Status----------------------------------------

def get_hikvision_cam_status(camera_ip):

    url = 'http://{}/ISAPI/System/time'.format(camera_ip)

    try:
        # Send request to fetch camera data
        response = requests.get(url, auth=HTTPDigestAuth(userid, password), verify=False)
        response.raise_for_status()
        
        if response.status_code == 200:
            print("Hikvision NVR Camera is active.")
        return "Active" 

#    except ConnectionError as e:
    except requests.exceptions.ConnectionError as e:
#        print("Connection error to Hikvision NVR Camera at IP:", camera_ip, "Error:", e)
        return "Inactive"

    except Exception as e:
#        print("Error initializing Hikvision NVR:", e)
        return "Inactive"


def main_hik_cam_status():
    # Get camera IPs from NVR
    #camera_ips = get_camera_ips_from_nvr()
    camera_ips = dahua_get_camera_ips_from_nvr()  # Fetch camera IPs from NVR
    if camera_ips:
        print("Camera IPs extracted:", camera_ips)
    else:
        print("No camera IPs found.")
        return
        
    #if get_hikvision_cam_status() == 'Active':
                
    # For each camera, extract camera status information
    hikvision_camera_status = []
    
    for camera_ip in camera_ips:
        camera_status = get_hikvision_cam_status(camera_ip)
        if camera_status == 'Active':
            hikvision_camera_status.append({
                "camera_ip": camera_ip,
                "camera_status": 'Active'
            })
        else:
            hikvision_camera_status.append({
                "camera_ip": camera_ip,
                "camera_status": None
            })
    # Prepare the final output in the desired format
    final_output = {
        "hikvision_camera_status": hikvision_camera_status
    }

    # Convert the result to a JSON string
    attributes_json = json.dumps(final_output)

    # Insert the JSON into the database (if necessary)
    if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
        insert_json_to_db(attributes_json)
#        print "Camera uptime status sent to database: {}".format(attributes_json)    

#    print "Final Camera uptime status Info: {}".format(attributes_json)    
        

#---------------------------------------------------------------------------------------------------------
 
if __name__ == "__main__":

#    time.sleep(1)
    #main_NVR_Record_Info()
    
    #hik_main_SDcard_Record_Info()
    #dahua_main_SDcard_Record_Info()    
    
    #hik_main_SDcard_Info()
    #dahua_main_SDcard_Info()
    
    #main_hik_cam_status()
    #main_dahua_cam_status()
    
    # Schedule the task to run every day at 5 PM
    schedule.every().day.at("17:00").do(main_NVR_Record_Info)
    
    # Schedule the task to run every day at 5:15 PM
    schedule.every().day.at("17:15").do(hik_main_SDcard_Record_Info)
    schedule.every().day.at("17:17").do(dahua_main_SDcard_Record_Info)
    
    # Schedule the task to run every day at 5:20 PM
    schedule.every().day.at("17:20").do(hik_main_SDcard_Info)
    schedule.every().day.at("17:22").do(dahua_main_SDcard_Info)
    
    # Schedule the task to run every Hr interval
    schedule.every(1).hours.do(main_hik_cam_status)
    #schedule.every(75).minutes.do(main_hik_cam_status)
    #schedule.every(1).hours.do(main_dahua_cam_status)
    schedule.every(63).minutes.do(main_dahua_cam_status)

    
#    watchdog.reset()  # Reset watchdog after 25 Hrs
    
    # Continuously run the scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(1)  # Sleep for a short time before checking again