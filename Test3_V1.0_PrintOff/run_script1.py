import subprocess

#script_path = "/home/pi/Test3/SerialCommunication.py"
#command = ['python', script_path, payload]
#result = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#subprocess.Popen(["python",'/home/pi/Test3/TLChronosProMAIN_391.py'])

subprocess.Popen(["python",'/home/pi/Test3/SerialCommunication.py'])
subprocess.Popen(["python",'/home/pi/Test3/serial_data_logger.py'])
subprocess.Popen(["python",'/home/pi/Test3/network_info.py'])
subprocess.Popen(["python",'/home/pi/Test3/TLChronosProMAIN_391.py'])
subprocess.Popen(["python",'/home/pi/Test3/thingsboard_mqtt_publisher.py'])

#import time 
#time.sleep(6000) #Sec
#subprocess.Popen(["python",'/home/pi/Test3/xml_parsing_9.py'])
#subprocess.Popen(["python",'/home/pi/Test3/hikvision1_biometric_14.py'])
