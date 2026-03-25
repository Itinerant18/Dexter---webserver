import subprocess

#script_path = "/home/pi/Test3/SerialCommunication.py"
#command = ['python', script_path, payload]
#result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#subprocess.Popen(["python",'/home/pi/Test3/TLChronosProMAIN_391.py'])


#import time 
#time.sleep(6000) #Sec
#subprocess.Popen(["python",'/home/pi/Test3/xml_parsing_9h.py'])
#subprocess.Popen(["python",'/home/pi/Test3/dahua_nvr_dvr_get_store_json_7h.py'])
subprocess.Popen(["python",'/home/pi/Test3/dahua_nvr_dvr_get_store_json_7i.py'])
subprocess.Popen(["python",'/home/pi/Test3/Extract_Logs_Dahua_41.py'])
subprocess.Popen(["python",'/home/pi/Test3/record_info_dahua.py'])



