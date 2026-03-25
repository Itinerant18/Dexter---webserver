import requests
from requests.auth import HTTPDigestAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime
import time
import schedule  # Import schedule
import json

from buffer_manager import insert_json_to_db

import device_parameters_module

import logical_params_module

# Initialize the database
logical_params_module.initialize_database()

#---------------------------Getting Parameters from Database---------------------------
device_type = 'HikvisionNVR1'
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

# NVR connection details
url = 'http://{}/ISAPI/System/time'.format(ipaddress)


# Function to get current time from the Hikvision NVR
def get_nvr_time():
    try:
        response = requests.get(url, auth=HTTPDigestAuth(userid, password), timeout=10)
        if response.status_code == 200:
            nvr_time_str = response.text.split("<localTime>")[1].split("</localTime>")[0]
            nvr_time = datetime.strptime(nvr_time_str, "%Y-%m-%dT%H:%M:%S+05:30")
            return nvr_time
        else:
            print("Failed to get NVR time. Status code:", response.status_code)
            return None
    except Exception as e:
        print("Error while getting NVR time:", e)
        return None

# Function to update the time on the Hikvision NVR
def update_nvr_time(local_time):
    # Construct XML payload to update the time
    xml_payload = """<Time version="1.0" xmlns="http://www.hikvision.com/ver20/XMLSchema">
        <timeMode>manual</timeMode>
        <localTime>{}</localTime>
        <timeZone>CST-5:30:00</timeZone>
        <windowsZone>India Standard Time</windowsZone>
    </Time>""".format(local_time)

    headers = {"Content-Type": "application/xml"}

    try:
        response = requests.put(url, data=xml_payload.strip(), headers=headers, auth=HTTPDigestAuth(userid, password), timeout=10)
        if response.status_code == 200:
            print("NVR time updated successfully.")
        else:
            print("Failed to update NVR time. Status code:", response.status_code)
    except Exception as e:
        print("Error while updating NVR time:", e)


def check_and_sync_time():
    global mismatch_counter

    print "\n[%s] Checking time sync..." % datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #system_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+05:30")
    system_time = datetime.now().replace(microsecond=0)
    
    nvr_time = get_nvr_time()
     
    if nvr_time:
        print "NVR Time   :", nvr_time
        print "System Time:", system_time

        time_diff = abs((system_time - nvr_time).total_seconds())
        if time_diff > 300:
            mismatch_counter += 1
            print("Time mismatch detected (count={}). Updating NVR time...".format(mismatch_counter))

            system_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+05:30")
            
            update_nvr_time(system_time)

            if mismatch_counter >= 3:
                print "Battery Low Warning: NVR time has drifted significantly 3 times in a row."
                mismatch_counter = 0

                # Prepare the log message
                log_data = {
                    "hik_nvr_battery_status": "batt_low"
                }

                try:
                    # Convert to JSON and insert into DB
                    attributes_json = json.dumps(log_data)

                    # Check integration flag before inserting
                    if logical_params_module.get_parameter("active_integration_hikvision_nvr") == 1:
                        insert_json_to_db(attributes_json)
                        print "Hikvision NVR battery status sent to database: {}".format(attributes_json)
                    else:
                        print "Hikvision NVR integration is disabled. Skipping database insert."
                except Exception as e:
                    print "Failed to insert hik nvr battery status into database:", str(e)

        else:
            print "System time and NVR time are synchronized."
            mismatch_counter = 0
    else:
        print "Skipping update due to NVR time fetch error."



# Main loop using schedule
if __name__ == "__main__":
    schedule.every(1).minutes.do(check_and_sync_time)
   # schedule.every(1).hours.do(check_and_sync_time)
    print "Scheduler started. Running time sync check every 1 hour..."

    #Run once immediately at startup
    check_and_sync_time()

    while True:
        schedule.run_pending()
        time.sleep(1)
