# -*- coding: utf-8 -*-
# !/usr/local/bin/python

import requests
from requests.auth import HTTPDigestAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

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

from datetime import datetime
#import datetime

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
                    "Module Reboot": "Dahua Logs",
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


# Fetch device parameters
device_type = 'DahuaNVR1'
devices = device_parameters_module.get_device_parameters(device_type)
ipaddress = devices[0][2]
userid = devices[0][3]
password = devices[0][4]

from buffer_manager import insert_json_to_db

# Define URLs
def build_url(ip, endpoint):
    return 'http://{}/cgi-bin/{}'.format(ip, endpoint)

# Function to authenticate and get logs
def extract_logs(ip, userid, password, start_time, end_time):
    try:
        # StartFind - Get token
        start_find_url = build_url(ip, "log.cgi?action=startFind&condition.StartTime={}&condition.EndTime={}".format(start_time, end_time))
        response = requests.get(start_find_url, auth=HTTPDigestAuth(userid, password), verify=False, timeout=10)

        if response.status_code == 401:
            print("Authentication failed. Please check the userid and password.")
            return
        elif response.status_code != 200:
            print("Failed to start log search. Status code:", response.status_code)
            return

        # Extract token from response
        response_data = response.text
        token = None
        if "token=" in response_data:
            token = response_data.split("token=")[1].strip()
        else:
            print("Token not found in response:", response_data)
            return

        print("Token obtained:", token)

        # DoFind - Fetch logs
        do_find_url = build_url(ip, "log.cgi?action=doFind&token={}&count=100".format(token))
        response = requests.get(do_find_url, auth=HTTPDigestAuth(userid, password), verify=False, timeout=10)

        if response.status_code != 200:
            print("Failed to fetch logs. Status code:", response.status_code)
            return

        # Parse and display logs
        log_data = response.text
        print("Logs retrieved:\n", log_data)
        return(log_data) 

    except requests.RequestException as e:
        print("An error occurred:", e)


def debug_logs(raw_data):
    import re
    from collections import defaultdict

    # Dictionary to store categorized log details
    log_summary = defaultdict(list)

    # Regular expressions for parsing
    log_entry_pattern = r"=== Log Entry ===\n(.+?)(?=\n=== Log Entry ===|\Z)"
    time_pattern = r"items\[\d+\]\.Time=(.+)"
    type_pattern = r"items\[\d+\]\.Type=(.+)"
    detail_pattern = r"items\[\d+\]\.Detail=(.+)"

    # Extract all log entries
    log_entries = re.findall(log_entry_pattern, raw_data, re.DOTALL)

    # Parse each log entry
    for entry in log_entries:
        time_match = re.search(time_pattern, entry)
        type_match = re.search(type_pattern, entry)
        detail_match = re.search(detail_pattern, entry)

        if time_match and type_match:
            log_time = time_match.group(1).strip()
            log_type = type_match.group(1).strip()

            if log_type in ["HDD Error", "Video Tampering", "CAM Offline Alarm"]:
                detail_text = detail_match.group(1).strip() if detail_match else ""
                log_summary[log_type].append("{0} at {1} - {2}".format(log_type, log_time, detail_text))

    # Construct the output
    output = []

    # Add HDD Error logs
    if log_summary["HDD Error"]:
        output.append("HDD Error:")
        output.extend(log_summary["HDD Error"])

    # Add Video Tampering logs
    if log_summary["Video Tampering"]:
        output.append("\nVideo Tampering:")
        output.extend(log_summary["Video Tampering"])

    # Add CAM Offline Alarm logs
    if log_summary["CAM Offline Alarm"]:
        output.append("\nCAM Offline Alarm:")
        output.extend(log_summary["CAM Offline Alarm"])

    # Join all parts for final output
    return "\n".join(output)


# Example usage
#raw_data = """[Your raw log data here]"""
#print(debug_logs(raw_data))


#import re
def parse_logs_0(log_data):
    print "Starting log parsing..."
    # Extracting all logs that contain a `Detail` field
    logs = re.findall(r"items\[\d+\]\..*?Detail=.*?(?=\nitems|\Z)", log_data, re.S)

    hdd_errors = []
    video_tampering_events = {}
    cam_offline_alarms = {}

    for i, log in enumerate(logs):
        print "\nProcessing log #{}: \n{}".format(i + 1, log)

        # Extracting Time, Type, and Detail
        log_time = re.search(r"Time=(.*?)\r?\n", log)
        log_type = re.search(r"Type=(.*?)\r?\n", log)
        log_detail = re.search(r"Detail=(.*?)(?:\nitems|\Z)", log, re.S)  # Ensure we capture all multiline details

        if not log_type or not log_time:
            print "Skipping log due to missing Type or Time..."
            continue

        event_time = log_time.group(1).strip()
        event_type = log_type.group(1).strip()
        detail = log_detail.group(1).strip() if log_detail else ""

        print ("Event Time:", event_time)
        print ("Event Type:", event_type)
        print ("Detail (raw):", repr(detail))  # Use repr to show invisible characters like \n

        if event_type == "HDD Error":
            hdd_errors.append("HDD Error at {}".format(event_time))
            print ("Added HDD Error:", hdd_errors[-1])

        elif event_type in ["Video Tampering", "CAM Offline Alarm"]:
            # Refined regex for extracting channel and action
            channel_match = re.search(r"Channel:\s*(\d+)", detail)
            action_match = re.search(r"Event Action:\s*(.*?)(?:\n|$)", detail)
            channel = channel_match.group(1).strip() if channel_match else "Unknown"
            action = action_match.group(1).strip() if action_match else "Unknown"

            print ("Extracted Details - Channel:", channel, "Action:", action)

            if event_type == "Video Tampering":
                if action == "Event Start":
                    video_tampering_events[channel] = {"start_time": event_time}
                    print "Video Tampering Event Start added for channel {}".format(channel)
                elif action == "Event End" and channel in video_tampering_events:
                    video_tampering_events[channel]["end_time"] = event_time
                    print "Video Tampering Event End added for channel {}".format(channel)

            elif event_type == "CAM Offline Alarm":
                if action == "Event Start":
                    cam_offline_alarms[channel] = {"start_time": event_time}
                    print "CAM Offline Alarm Event Start added for channel {}".format(channel)
                elif action == "Event End" and channel in cam_offline_alarms:
                    cam_offline_alarms[channel]["end_time"] = event_time
                    print "CAM Offline Alarm Event End added for channel {}".format(channel)

    # Compiling results
    result = []

    # HDD Errors
    result.append("HDD Error:")
    result.extend(hdd_errors)

    # Video Tampering Logs
    result.append("\nVideo Tampering:")
    for channel, times in video_tampering_events.items():
        start_time = times.get("start_time", "Unknown")
        end_time = times.get("end_time", "Unknown")
        if start_time != "Unknown" and end_time != "Unknown":
            result.append("Event Start on Channel {} at {}".format(channel, start_time))
            result.append("Event End on Channel {} at {}".format(channel, end_time))
        elif start_time != "Unknown":
            result.append("Event Start on Channel {} at {}".format(channel, start_time))

    # CAM Offline Alarm Logs
    result.append("\nCAM Offline Alarm:")
    for channel, times in cam_offline_alarms.items():
        start_time = times.get("start_time", "Unknown")
        end_time = times.get("end_time", "Unknown")
        if start_time != "Unknown" and end_time != "Unknown":
            result.append("Event Start on Channel {} at {}".format(channel, start_time))
            result.append("Event End on Channel {} at {}".format(channel, end_time))
        elif start_time != "Unknown":
            result.append("Event Start on Channel {} at {}".format(channel, start_time))

    print "\nFinished parsing logs. Compiled results:"
    for line in result:
        print line

    return "\n".join(result)


import re
def parse_logs(log_data):
    print "Starting log parsing..."
    # Extracting all logs that contain a `Detail` field
    logs = re.findall(r"items\[\d+\]\..*?Detail=.*?(?=\nitems|\Z)", log_data, re.S)

    hdd_errors = []
    video_tampering_events = {}
    cam_offline_alarms = {}

    for i, log in enumerate(logs):
        print "\nProcessing log #{}: \n{}".format(i + 1, log)

        # Extracting Time, Type, and Detail
        log_time = re.search(r"Time=(.*?)\r?\n", log)
        log_type = re.search(r"Type=(.*?)\r?\n", log)
        log_detail = re.search(r"Detail=(.*?)(?:\nitems|\Z)", log, re.S)  # Ensure we capture all multiline details

        if not log_type or not log_time:
            print "Skipping log due to missing Type or Time..."
            continue

        event_time = log_time.group(1).strip()
        event_type = log_type.group(1).strip()
        detail = log_detail.group(1).strip() if log_detail else ""

        print ("Event Time:", event_time)
        print ("Event Type:", event_type)
        print ("Detail (raw):", repr(detail))  # Use repr to show invisible characters like \n

        if event_type == "HDD Error":
            hdd_errors.append("HDD Error at {}".format(event_time))
            print ("Added HDD Error:", hdd_errors[-1])

        elif event_type in ["Video Tampering", "CAM Offline Alarm"]:
            # Refined regex for extracting channel and action
            channel_match = re.search(r"Channel:\s*(\d+)", detail)
            action_match = re.search(r"Event Action:\s*(.*?)(?:\n|$)", detail)
            channel = channel_match.group(1).strip() if channel_match else "Unknown"
            action = action_match.group(1).strip() if action_match else "Unknown"

            print ("Extracted Details - Channel:", channel, "Action:", action)

            if event_type == "Video Tampering":
                if action == "Event Start":
                    video_tampering_events[channel] = {"start_time": event_time}
                    print "Video Tampering Event Start added for channel {}".format(channel)
                elif action == "Event End":
                    if channel in video_tampering_events:
                        video_tampering_events[channel]["end_time"] = event_time
                    else:
                        video_tampering_events[channel] = {"end_time": event_time}
                    print "Video Tampering Event End processed for channel {}".format(channel)

            elif event_type == "CAM Offline Alarm":
                if action == "Event Start":
                    cam_offline_alarms[channel] = {"start_time": event_time}
                    print "CAM Offline Alarm Event Start added for channel {}".format(channel)
                elif action == "Event End":
                    if channel in cam_offline_alarms:
                        cam_offline_alarms[channel]["end_time"] = event_time
                    else:
                        cam_offline_alarms[channel] = {"end_time": event_time}
                    print "CAM Offline Alarm Event End processed for channel {}".format(channel)

    # Compiling results
    result = []

    # HDD Errors
    result.append("HDD Error:")
    result.extend(hdd_errors)

    # Video Tampering Logs
    result.append("\nVideo Tampering:")
    for channel, times in video_tampering_events.items():
        start_time = times.get("start_time", "Unknown")
        end_time = times.get("end_time", "Unknown")
        if start_time != "Unknown" and end_time != "Unknown":
            result.append("Event Start on Channel {} at {}".format(channel, start_time))
            result.append("Event End on Channel {} at {}".format(channel, end_time))
        elif start_time != "Unknown":
            result.append("Event Start on Channel {} at {}".format(channel, start_time))
        elif end_time != "Unknown":
            result.append("Event End on Channel {} at {}".format(channel, end_time))

    # CAM Offline Alarm Logs
    result.append("\nCAM Offline Alarm:")
    for channel, times in cam_offline_alarms.items():
        start_time = times.get("start_time", "Unknown")
        end_time = times.get("end_time", "Unknown")
        if start_time != "Unknown" and end_time != "Unknown":
            result.append("Event Start on Channel {} at {}".format(channel, start_time))
            result.append("Event End on Channel {} at {}".format(channel, end_time))
        elif start_time != "Unknown":
            result.append("Event Start on Channel {} at {}".format(channel, start_time))
        elif end_time != "Unknown":
            result.append("Event End on Channel {} at {}".format(channel, end_time))

    print "\nFinished parsing logs. Compiled results:"
    for line in result:
        print line

    return "\n".join(result)


#camera_tampered
#camera_tampered_restored

#camera_disconnect
#camera_connection_established

#hdd_error
#hdd_error_restored

#from datetime import datetime

def parse_logs_array_dictionary_0(input_data):
    """
    Parses the input log data and converts it into a list of dictionaries 
    with specified fields.
    
    Args:
        input_data (str): Multiline string containing the log data.
    
    Returns:
        list: A list of dictionaries with parsed log information.
    """
    # Helper function to format date and time
    def format_date_time(timestamp):
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d%m%y"), dt.strftime("%H%M")

    parsed_logs = []

    # Process HDD Error
    hdd_errors = [
        line.split(" at ")[1] for line in input_data.splitlines()
        if line.startswith("HDD Error at")
    ]
    for error_time in hdd_errors:
        date, time = format_date_time(error_time)
        parsed_logs.append({
            "zone_no": None,
            "channelID": None,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": "hdd_error"
        })

    # Process Video Tampering
    video_tampering = [
        line for line in input_data.splitlines() if line.startswith("Event")
    ]
    for line in video_tampering:
        parts = line.split(" ")
        event_type = "camera_tampered" if "Start" in line else "camera_tampered_restored"
        channel_id = parts[4]
        timestamp = parts[6] + " " + parts[7]
        date, time = format_date_time(timestamp)
        parsed_logs.append({
            "zone_no": None,
            "channelID": channel_id,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": event_type
        })

    # Process CAM Offline Alarm
    cam_alarms = [
        line for line in input_data.splitlines() if line.startswith("Event")
        and "CAM Offline Alarm" in input_data.splitlines()
    ]
    for line in cam_alarms:
        parts = line.split(" ")
        event_type = "camera_disconnect" if "Start" in line else "camera_connection_established"
        channel_id = parts[4]
        timestamp = parts[6] + " " + parts[7]
        date, time = format_date_time(timestamp)
        parsed_logs.append({
            "zone_no": None,
            "channelID": channel_id,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": event_type
        })

    return parsed_logs



#from datetime import datetime

def parse_logs_array_dictionary_1(input_data):
    """
    Parses the input log data and converts it into a list of dictionaries 
    with specified fields.
    
    Args:
        input_data (str): Multiline string containing the log data.
    
    Returns:
        list: A list of dictionaries with parsed log information.
    """
    # Helper function to format date and time
    def format_date_time(timestamp):
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d%m%y"), dt.strftime("%H%M")

    parsed_logs = []

    # Process HDD Error
    hdd_errors = [
        line.split(" at ")[1] for line in input_data.splitlines()
        if line.startswith("HDD Error at")
    ]
    for error_time in hdd_errors:
        date, time = format_date_time(error_time)
        parsed_logs.append({
            "zone_no": None,
            "channelID": None,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": "HDD Error"
        })

    # Process Video Tampering and CAM Offline Alarm separately
    for line in input_data.splitlines():
        if line.startswith("Event Start") or line.startswith("Event End"):
            parts = line.split(" ")
            event_type = "camera_tampered" if "Video Tampering" in input_data else "cam_offline_alarm"
            event_type += "_end" if "End" in line else ""
            channel_id = parts[4]
            timestamp = parts[6] + " " + parts[7]
            date, time = format_date_time(timestamp)
            parsed_logs.append({
                "zone_no": None,
                "channelID": channel_id,
                "branch": None,
                "time": time,
                "date": date,
                "log_type": event_type
            })

    return parsed_logs



#from datetime import datetime

def parse_logs_array_dictionary_2(input_data):
    """
    Parses the input log data and converts it into a list of dictionaries 
    with specified fields.
    
    Args:
        input_data (str): Multiline string containing the log data.
    
    Returns:
        list: A list of dictionaries with parsed log information.
    """
    # Helper function to format date and time
    def format_date_time(timestamp):
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d%m%y"), dt.strftime("%H%M")

    parsed_logs = []

    # Process HDD Error
    hdd_errors = [
        line.split(" at ")[1] for line in input_data.splitlines()
        if line.startswith("HDD Error at")
    ]
    for error_time in hdd_errors:
        date, time = format_date_time(error_time)
        parsed_logs.append({
            "zone_no": None,
            "channelID": None,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": "HDD Error"
        })

    # Process Video Tampering
    video_tampering = [
        line for line in input_data.splitlines()
        if line.startswith("Event") and "Channel" in line and "Video Tampering" in input_data
    ]
    for line in video_tampering:
        parts = line.split(" ")
        event_type = "camera_tampered" if "Start" in line else "camera_tampered_end"
        channel_id = parts[4]
        timestamp = parts[6] + " " + parts[7]
        date, time = format_date_time(timestamp)
        parsed_logs.append({
            "zone_no": None,
            "channelID": channel_id,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": event_type
        })

    # Process CAM Offline Alarm
    cam_alarms = [
        line for line in input_data.splitlines()
        if line.startswith("Event") and "Channel" in line and "CAM Offline Alarm" in input_data
    ]
    for line in cam_alarms:
        parts = line.split(" ")
        event_type = "cam_offline_alarm" if "Start" in line else "cam_offline_alarm_end"
        channel_id = parts[4]
        timestamp = parts[6] + " " + parts[7]
        date, time = format_date_time(timestamp)
        parsed_logs.append({
            "zone_no": None,
            "channelID": channel_id,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": event_type
        })

    return parsed_logs


#from datetime import datetime

def parse_logs_array_dictionary_3(input_data):
    """
    Parses the input log data and converts it into a list of dictionaries 
    with specified fields.
    
    Args:
        input_data (str): Multiline string containing the log data.
    
    Returns:
        list: A list of dictionaries with parsed log information.
    """
    # Helper function to format date and time
    def format_date_time(timestamp):
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d%m%y"), dt.strftime("%H%M")

    parsed_logs = []

    # Process HDD Error
    hdd_errors = [
        line.split(" at ")[1] for line in input_data.splitlines()
        if line.startswith("HDD Error at")
    ]
    for error_time in hdd_errors:
        date, time = format_date_time(error_time)
        parsed_logs.append({
            "zone_no": None,
            "channelID": None,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": "HDD Error"
        })

    # Process Video Tampering
    video_tampering = [
        line for line in input_data.splitlines()
        if line.startswith("Event") and "Channel" in line and "Video Tampering" in line
    ]
    for line in video_tampering:
        parts = line.split(" ")
        event_type = "video_tampering_start" if "Start" in line else "video_tampering_end"
        channel_id = parts[4]
        timestamp = parts[6] + " " + parts[7]
        date, time = format_date_time(timestamp)
        parsed_logs.append({
            "zone_no": None,
            "channelID": channel_id,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": event_type
        })

    # Process CAM Offline Alarm
    cam_alarms = [
        line for line in input_data.splitlines()
        if line.startswith("Event") and "Channel" in line and "CAM Offline Alarm" in line
    ]
    for line in cam_alarms:
        parts = line.split(" ")
        event_type = "cam_offline_alarm_start" if "Start" in line else "cam_offline_alarm_end"
        channel_id = parts[4]
        timestamp = parts[6] + " " + parts[7]
        date, time = format_date_time(timestamp)
        parsed_logs.append({
            "zone_no": None,
            "channelID": channel_id,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": event_type
        })

    return parsed_logs


def parse_logs_array_dictionary_4(input_data):
    """
    Parses the input log data and converts it into a list of dictionaries 
    with specified fields.
    
    Args:
        input_data (str): Multiline string containing the log data.
    
    Returns:
        list: A list of dictionaries with parsed log information.
    """
    # Helper function to format date and time
    def format_date_time(timestamp):
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d%m%y"), dt.strftime("%H%M")

    parsed_logs = []

    # Process HDD Error
    hdd_errors = [
        line.split(" at ")[1] for line in input_data.splitlines()
        if line.startswith("HDD Error at")
    ]
    for error_time in hdd_errors:
        date, time = format_date_time(error_time)
        parsed_logs.append({
            "zone_no": None,
            "channelID": None,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": "HDD Error"
        })

    # Process Video Tampering
    video_tampering = [
        line for line in input_data.splitlines()
        if line.startswith("Event") and "Channel" in line and "Video Tampering" in input_data
    ]
    for line in video_tampering:
        parts = line.split(" ")
        event_type = "camera_tampered" if "Start" in line else "camera_tampered_end"
        channel_id = parts[4]
        timestamp = parts[6] + " " + parts[7]
        date, time = format_date_time(timestamp)
        parsed_logs.append({
            "zone_no": None,
            "channelID": channel_id,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": event_type
        })

    # Process CAM Offline Alarm
    cam_alarms = [
        line for line in input_data.splitlines()
        if line.startswith("Event") and "Channel" in line and "CAM Offline Alarm" in input_data
    ]
    for line in cam_alarms:
        parts = line.split(" ")
        event_type = "cam_offline_alarm" if "Start" in line else "cam_offline_alarm_end"
        channel_id = parts[4]
        timestamp = parts[6] + " " + parts[7]
        date, time = format_date_time(timestamp)
        parsed_logs.append({
            "zone_no": None,
            "channelID": channel_id,
            "branch": None,
            "time": time,
            "date": date,
            "log_type": event_type
        })

    return parsed_logs


#from datetime import datetime

#camera_tampered
#camera_tampered_restored

#camera_disconnect
#camera_connection_established

#hdd_error
#hdd_error_restored

def parse_logs_array_dictionary(input_data):
    """
    Parses the input log data and converts it into a list of dictionaries 
    with specified fields.
    
    Args:
        input_data (str): Multiline string containing the log data.
    
    Returns:
        list: A list of dictionaries with parsed log information.
    """
    def format_date_time(timestamp):
        dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return dt.strftime("%d%m%y"), dt.strftime("%H%M")
    
    parsed_logs = []

    # Split input data into sections
    sections = input_data.split("\n\n")
    for section in sections:
        lines = section.strip().splitlines()

        # Parse HDD Errors
        if lines[0].startswith("HDD Error:"):
            for line in lines[1:]:
                if "HDD Error at" in line:
                    timestamp = line.split(" at ")[1]
                    date, time = format_date_time(timestamp)
                    parsed_logs.append({
                        "zone_no": None,
                        "channelID": None,
                        "branch": None,
                        "time": time,
                        "date": date,
                        "log_type": "hdd_error"
                    })

        # Parse Video Tampering Events
        elif lines[0].startswith("Video Tampering:"):
            for line in lines[1:]:
                if "Event Start" in line:
                    parts = line.split(" ")
                    channel_id = parts[4]
                    timestamp = parts[6] + " " + parts[7]
                    date, time = format_date_time(timestamp)
                    parsed_logs.append({
                        "zone_no": None,
                        "channelID": channel_id,
                        "branch": None,
                        "time": time,
                        "date": date,
                        "log_type": "camera_tampered"
                    })
                elif "Event End" in line:
                    parts = line.split(" ")
                    channel_id = parts[4]
                    timestamp = parts[6] + " " + parts[7]
                    date, time = format_date_time(timestamp)
                    parsed_logs.append({
                        "zone_no": None,
                        "channelID": channel_id,
                        "branch": None,
                        "time": time,
                        "date": date,
                        "log_type": "camera_tampered_restored"
                    })

        # Parse CAM Offline Alarms
        elif lines[0].startswith("CAM Offline Alarm:"):
            for line in lines[1:]:
                if "Event Start" in line:
                    parts = line.split(" ")
                    channel_id = parts[4]
                    timestamp = parts[6] + " " + parts[7]
                    date, time = format_date_time(timestamp)
                    parsed_logs.append({
                        "zone_no": None,
                        "channelID": channel_id,
                        "branch": None,
                        "time": time,
                        "date": date,
                        "log_type": "camera_disconnect"
                    })
                elif "Event End" in line:
                    parts = line.split(" ")
                    channel_id = parts[4]
                    timestamp = parts[6] + " " + parts[7]
                    date, time = format_date_time(timestamp)
                    parsed_logs.append({
                        "zone_no": None,
                        "channelID": channel_id,
                        "branch": None,
                        "time": time,
                        "date": date,
                        "log_type": "camera_connection_established"
                    })

    return parsed_logs




import time

def parse_logs_filtered_0(logs):
    # Initialize an empty list for the new dictionary elements
    new_logs = []
    
    # Track whether we have added an 'hdd_error' entry
    hdd_error_added = False
    
    # Loop through the given logs
    for log in logs:
        if log['log_type'] == 'hdd_error':
            # If an 'hdd_error' entry hasn't been added yet, add it
            if not hdd_error_added:
                new_logs.append(log)
                hdd_error_added = True
        else:
            # Add non-'hdd_error' entries directly to the new logs
            new_logs.append(log)
    
    # If no 'hdd_error' entries were found, add the 'hdd_error_restored' log
    if not hdd_error_added:
        current_time = time.strftime("%H%M")
        current_date = time.strftime("%d%m%y")
        restored_log = {
            'zone_no': None,
            'channelID': None,
            'branch': None,
            'time': current_time,
            'date': current_date,
            'log_type': 'hdd_error_restored'
        }
        new_logs.append(restored_log)
    
    return new_logs


import time

#last_log_type = None

def parse_logs_filtered_1(logs):
    # Initialize an empty list for the new dictionary elements
    new_logs = []
    
    # Track whether we have added an 'hdd_error' entry
    hdd_error_added = False
    
    # Track the last log type
    #last_log_type = None
    global last_log_type
    
    # Loop through the given logs
    for log in logs:
        if log['log_type'] == 'hdd_error':
            # If an 'hdd_error' entry hasn't been added yet, add it
            if not hdd_error_added:
                new_logs.append(log)
                hdd_error_added = True
                last_log_type = 'hdd_error'
        elif log['log_type'] == 'hdd_error_restored':
            # Add 'hdd_error_restored' only if the last log wasn't the same
            if last_log_type != 'hdd_error_restored':
                new_logs.append(log)
                last_log_type = 'hdd_error_restored'
        else:
            # Add non-'hdd_error' entries directly to the new logs
            new_logs.append(log)
            last_log_type = log['log_type']
    
    # If no 'hdd_error' entries were found, add the 'hdd_error_restored' log
    if not hdd_error_added and last_log_type != 'hdd_error_restored':
        current_time = time.strftime("%H%M")
        current_date = time.strftime("%d%m%y")
        restored_log = {
            'zone_no': None,
            'channelID': None,
            'branch': None,
            'time': current_time,
            'date': current_date,
            'log_type': 'hdd_error_restored'
        }
        new_logs.append(restored_log)
    
    return new_logs


# Global variable to persist the last log type
#last_log_type = None

def parse_logs_filtered_2(logs):
    global last_log_type  # Use the global variable
    
    new_logs = []
    hdd_error_added = False

    for log in logs:
        if log['log_type'] == 'hdd_error':
            if not hdd_error_added:
                new_logs.append(log)
                hdd_error_added = True
                last_log_type = 'hdd_error'
        elif log['log_type'] == 'hdd_error_restored':
            if last_log_type != 'hdd_error_restored':
                new_logs.append(log)
                last_log_type = 'hdd_error_restored'
        else:
            new_logs.append(log)
            last_log_type = log['log_type']
    
    # If no 'hdd_error' was added and the last log wasn't 'hdd_error_restored'
    if not hdd_error_added and last_log_type != 'hdd_error_restored':
        import time
        current_time = time.strftime("%H%M")
        current_date = time.strftime("%d%m%y")
        restored_log = {
            'zone_no': None,
            'channelID': None,
            'branch': None,
            'time': current_time,
            'date': current_date,
            'log_type': 'hdd_error_restored'
        }
        new_logs.append(restored_log)
        last_log_type = 'hdd_error_restored'

    return new_logs




# Global variable to persist the last log type
#last_log_type = None

def parse_logs_filtered_3(logs):
    global last_log_type  # Use the global variable

    new_logs = []
    hdd_error_added = False

    for log in logs:
        if log['log_type'] == 'hdd_error':
            if not hdd_error_added:
                new_logs.append(log)
                hdd_error_added = True
                last_log_type = 'hdd_error'
        elif log['log_type'] == 'hdd_error_restored':
            # Only add if the last log type is not 'hdd_error_restored'
            if last_log_type != 'hdd_error_restored':
                new_logs.append(log)
                last_log_type = 'hdd_error_restored'
        else:
            # Handle other log types
            new_logs.append(log)
            last_log_type = log['log_type']

    # Only add 'hdd_error_restored' if:
    # - No 'hdd_error' log was added
    # - The last log wasn't 'hdd_error_restored'
    # - No 'hdd_error_restored' is already in the new logs
    if not hdd_error_added and last_log_type != 'hdd_error_restored':
        already_restored = any(log['log_type'] == 'hdd_error_restored' for log in new_logs)
        if not already_restored:
            import time
            current_time = time.strftime("%H%M")
            current_date = time.strftime("%d%m%y")
            restored_log = {
                'zone_no': None,
                'channelID': None,
                'branch': None,
                'time': current_time,
                'date': current_date,
                'log_type': 'hdd_error_restored'
            }
            new_logs.append(restored_log)
            last_log_type = 'hdd_error_restored'

    return new_logs



# Global variable to track if 'hdd_error_restored' was already sent
last_log_type = None
hdd_restored_sent = False  # Tracks whether 'hdd_error_restored' has been generated

def parse_logs_filtered(logs):
    global last_log_type, hdd_restored_sent

    new_logs = []
    hdd_error_added = False

    for log in logs:
        if log['log_type'] == 'hdd_error':
            if not hdd_error_added:
                new_logs.append(log)
                hdd_error_added = True
                last_log_type = 'hdd_error'
                hdd_restored_sent = False  # Reset as new 'hdd_error' is logged
        elif log['log_type'] == 'hdd_error_restored':
            if not hdd_restored_sent:
                new_logs.append(log)
                last_log_type = 'hdd_error_restored'
                hdd_restored_sent = True
        else:
            # For other log types, add them but don't reset hdd_restored_sent
            new_logs.append(log)
            last_log_type = log['log_type']

    # Append 'hdd_error_restored' if:
    # - No 'hdd_error' logs were added
    # - The last log wasn't 'hdd_error_restored'
    # - It hasn't been sent already
    if not hdd_error_added and not hdd_restored_sent:
        import time
        current_time = time.strftime("%H%M")
        current_date = time.strftime("%d%m%y")
        restored_log = {
            'zone_no': None,
            'channelID': None,
            'branch': None,
            'time': current_time,
            'date': current_date,
            'log_type': 'hdd_error_restored'
        }
        new_logs.append(restored_log)
        last_log_type = 'hdd_error_restored'
        hdd_restored_sent = True

    return new_logs



# Sample dictionary list
#logs = [
#    {'zone_no': None, 'channelID': None, 'branch': None, 'time': '0944', 'date': '080125', 'log_type': 'hdd_error'},
#    {'zone_no': None, 'channelID': None, 'branch': None, 'time': '0955', 'date': '080125', 'log_type': 'camera_tampered'},
#    {'zone_no': None, 'channelID': '2', 'branch': None, 'time': '0957', 'date': '080125', 'log_type': 'camera_disconnect'}
#]

# Call the function
#result = parse_logs(logs)

# Print the result
#print(result)




# Example input data
input_data1 = """
HDD Error:
HDD Error at 2025-01-02 16:14:05
HDD Error at 2025-01-02 16:14:10
HDD Error at 2025-01-02 16:14:15

Video Tampering:
Event Start on Channel 2 at 2025-01-02 16:19:12
Event End on Channel 2 at 2025-01-02 16:19:16

CAM Offline Alarm:
Event Start on Channel 6 at 2025-01-02 16:19:40
Event End on Channel 6 at 2025-01-02 16:21:21
"""

#Call the function and print the result
#parsed_logs = parse_logs_array_dictionary(input_data1)
#print(parsed_logs)


#import datetime

def generate_time_difference_0(minutes_to_deduct):
    """
    Generate the current time as start_time and calculate the end_time by subtracting
    the specified number of minutes.

    Args:
        minutes_to_deduct (int): Number of minutes to subtract from the current time.

    Returns:
        dict: A dictionary containing the start time and the end time.
    """

    import datetime
    
    try:
        # Get the current time as the start_time
        start_time = datetime.datetime.now()
        
        # Calculate the end_time by subtracting the specified minutes
        end_time = start_time - datetime.timedelta(minutes=minutes_to_deduct)
        
        # Format the times as strings
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            "start_time": start_time_str,
            "end_time": end_time_str
        }
    except Exception as e:
        return {"error": str(e)}


#import datetime
# Global variable to store the start time of the previous iteration
#prev_start_time = None

def generate_time_difference_1(minutes_to_deduct):
    """
    Generate the current time as start_time (for the first iteration) or use the previous
    start time as end_time for subsequent iterations. Calculate end_time by subtracting
    the specified number of minutes from the start_time.

    Args:
        minutes_to_deduct (int): Number of minutes to subtract for the time difference.

    Returns:
        dict: A dictionary containing the start time and the end time.
    """
    import datetime
    
    global prev_start_time  # Access the global variable

    try:
        if prev_start_time is None:
            # For the first iteration, use the current time as start_time
            start_time = datetime.datetime.now()
        else:
            # For subsequent iterations, use the previous start time as the new end_time
            start_time = prev_start_time

        # Calculate the end_time by subtracting the specified minutes
        end_time = start_time - datetime.timedelta(minutes=minutes_to_deduct)

        # Add an offset of 1 second to the end_time
        end_time += datetime.timedelta(seconds=1)

        # Format the times as strings
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        # Update the global variable for the next iteration
        prev_start_time = start_time + datetime.timedelta(minutes=1)  # Increment for next iteration

        return {
            "start_time": start_time_str,
            "end_time": end_time_str
        }
    except Exception as e:
        return {"error": str(e)}


# Global variable to store the history of start times
#start_time_history = []

def generate_time_difference_2(minutes_to_deduct):
    """
    Generate the current start_time based on the last recorded start time,
    ensuring the difference matches the specified interval. Calculate the 
    end_time by subtracting the specified number of minutes.

    Args:
        minutes_to_deduct (int): Number of minutes to subtract for the interval.

    Returns:
        dict: A dictionary containing the start time and the end time.
    """
    import datetime
    
    global start_time_history

    try:
        # Check if history exists; if not, use the current time as the base
        if not start_time_history:
            current_time = datetime.datetime.now()
        else:
            # Calculate the next start time based on the last recorded time
            current_time = start_time_history[-1] + datetime.timedelta(minutes=minutes_to_deduct)

        # Record the current time in history
        start_time_history.append(current_time)

        # Calculate the end time
        end_time = current_time - datetime.timedelta(minutes=minutes_to_deduct)

        # Format the times as strings
        start_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "start_time": start_time_str,
            "end_time": end_time_str
        }
    except Exception as e:
        return {"error": str(e)}



# Global variable to store the history of start times
start_time_history = []

def generate_time_difference(minutes_to_deduct):
    """
    Generate the current start_time based on the last recorded start time,
    ensuring the difference matches the specified interval. Calculate the 
    end_time by subtracting the specified number of minutes. Adds one second 
    to the calculated current time.

    Args:
        minutes_to_deduct (int): Number of minutes to subtract for the interval.

    Returns:
        dict: A dictionary containing the start time and the end time.
    """

    import datetime
    
    global start_time_history

    try:
        # Check if history exists; if not, use the current time as the base
        if not start_time_history:
            current_time = datetime.datetime.now()
        else:
            # Calculate the next start time based on the last recorded time plus minutes_to_deduct and 1 second
            current_time = start_time_history[-1] + datetime.timedelta(minutes=minutes_to_deduct, seconds=1)

        # Record the current time in history
        start_time_history.append(current_time)

        # Calculate the end time
        end_time = current_time - datetime.timedelta(minutes=minutes_to_deduct)

        # Format the times as strings
        start_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "start_time": start_time_str,
            "end_time": end_time_str
        }
    except Exception as e:
        return {"error": str(e)}


# Example usage
#minutes_to_deduct = 37  # Replace with the desired number of minutes to deduct
#result = generate_time_difference(minutes_to_deduct)

#print("Start Time:", result["start_time"])
#print("End Time:", result["end_time"])



# Function to process and display log entries
def process_log_entries(log_entries):
    # Check if the input list is not empty
    if not log_entries:
        return  # Do nothing if the list is empty

    # Loop through the list of log entries
    for i, entry in enumerate(log_entries):
        if not entry:  # Skip if the dictionary is empty
            continue

        print("Log Entry {}:".format(i + 1))
        for key, value in entry.items():
            print("  {}: {}".format(key, value))
        
        # Call another function for further processing
        subsequent_processing(entry)
        #print()


# Call the main function
#process_log_entries(log_entries)

# Function to handle subsequent processing of individual log entries
def subsequent_processing(entry):
    # Example: Process or save the log entry

    attributes_json = json.dumps(entry)
    if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:    
        insert_json_to_db(attributes_json)
    print("Please check LATEST TELEMETRY field of your device")
    print(attributes_json)


# Example usage
if __name__ == "__main__":
    # Define the log retrieval time range
    #start_time = "2025-01-02 16:14:00"
    #end_time = "2025-01-02 16:24:00"

    #start_time = "2025-01-04 11:55:00"
    #end_time = "2025-01-04 12:32:00"


    #start_time = "2025-01-06 14:27:28"
    #end_time = "2025-01-06 14:37:27"

    minutes_to_deduct = 5  # Replace with the desired number of minutes to deduct

    while True:
    #def scan():
    
        result = generate_time_difference(minutes_to_deduct)

        #print("Result")
        #print(result)

        end_time = result["start_time"]
        start_time = result["end_time"]

        print("Start Time:", result["start_time"])
        print("End Time:", result["end_time"])

        # Extract logs
        response = extract_logs(ipaddress, userid, password, start_time, end_time)
        print(" Output ")
        #print(response)

        #debug_logs(response)  # To verify if logs are parsed correctly

        print(" ---------- LOGS ---------- ")
        
        watchdog.reset()  # Reset watchdog after 30min

        try:
            # Use regex to find logs

            parsed_output0 = parse_logs(response)

            print(" ------- CONSOLIDATED ----- ")    
            print(parsed_output0)

            #print(debug_logs(response))

            print(" --------  PARSED --------- ")
            #parsed_logs = parse_logs_array_dictionary(input_data)
            parsed_logs = parse_logs_array_dictionary(parsed_output0)
            print(parsed_logs)


            print(" --------  PARSED FILTERED --------- ")
            # Call the function
            result = parse_logs_filtered(parsed_logs)

            # Print the result
            print(result)


            process_log_entries(result)
           
            #return logs
        except Exception as e:
        
            print("Error during log parsing: {}".format(e))
            pass

        time.sleep( (minutes_to_deduct) * 60)

    #scan()
