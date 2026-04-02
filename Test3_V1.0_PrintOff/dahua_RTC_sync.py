import requests
from requests.auth import HTTPDigestAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime
import urllib3
import time
import schedule  # Import schedule
import json

from buffer_manager import insert_json_to_db

import device_parameters_module

import logical_params_module

# Initialize the database
logical_params_module.initialize_database()

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

# Global counter for mismatches
mismatch_counter = 0

# Function to get current time from Dahua NVR
def get_dahua_nvr_time():
    try:
        url = 'https://{}/cgi-bin/global.cgi?action=getCurrentTime'.format(ipaddress)
        response = requests.get(url,
                              auth=HTTPDigestAuth(userid, password),
                              verify=False)  # SSL verification disabled
        response.raise_for_status()

        # Parse the result string: result=YYYY-MM-DD HH:MM:SS
        if "result=" in response.text:
            nvr_time_str = response.text.split("result=")[1].strip()
            nvr_time = datetime.strptime(nvr_time_str, "%Y-%m-%d %H:%M:%S")
            return nvr_time
        else:
            print("Unexpected response format:", response.text)
            return None
    except Exception as e:
        print("Failed to get NVR time:", e)
        return None


# Function to update NVR time
def set_dahua_nvr_time(system_time):
    try:
        formatted_time = system_time.strftime("%Y-%m-%d%%20%H:%M:%S")  # URL encoded space
        url = 'https://{}/cgi-bin/global.cgi?action=setCurrentTime&time={}'.format(ipaddress,formatted_time)
        response = requests.get(url,
                              auth=HTTPDigestAuth(userid, password),
                              verify=False)  # SSL verification disabled
        response.raise_for_status()

        print("NVR time updated successfully.")
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
    except Exception as e:
        print("Failed to set NVR time:", e)


def check_and_sync_time_dahua():
    global mismatch_counter

    print "\n[%s] Checking time sync..." % datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get system time (rounded to seconds)
    system_time = datetime.now().replace(microsecond=0)
    nvr_time = get_dahua_nvr_time()

    if nvr_time:
        print "NVR Time   :", nvr_time
        print "System Time:", system_time

        time_diff = abs((system_time - nvr_time).total_seconds())
        if time_diff > 300:
            mismatch_counter += 1
            print("Time mismatch detected (count={}). Updating NVR time...".format(mismatch_counter))
            set_dahua_nvr_time(system_time)

            if mismatch_counter >= 3:
                print "Battery Low Warning: NVR time has drifted significantly 3 times in a row."
                mismatch_counter = 0

                # Prepare the log message
                log_data = {
                    "dahua_nvr_battery_status": "nvr_batt_low"
                }

                try:
                    # Convert to JSON and insert into DB
                    attributes_json = json.dumps(log_data)

                    # Check integration flag before inserting
                    if logical_params_module.get_parameter("active_integration_dahua_nvr") == 1:
                        insert_json_to_db(attributes_json)
                        print "Dahua NVR battery status sent to database: {}".format(attributes_json)
                    else:
                        print "Dahua NVR integration is disabled. Skipping database insert."
                except Exception as e:
                    print "Failed to insert hik nvr battery status into database:", str(e)

        else:
            print "System time and NVR time are synchronized."
            mismatch_counter = 0
    else:
        print "Skipping update due to NVR time fetch error."



# Main loop using schedule
if __name__ == "__main__":
    
    # Schedule the function to run every 5 minutes
#    schedule.every(5).minutes.do(check_and_sync_time_dahua)
    
    schedule.every(1).hours.do(check_and_sync_time_dahua)

    print "Scheduler started. Running time sync check every 1 hour..."

    # Run once immediately at startup
    check_and_sync_time_dahua()

    while True:
        schedule.run_pending()
        time.sleep(1)

