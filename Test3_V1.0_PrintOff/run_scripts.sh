#!/bin/bash
/usr/bin/python2 /home/pi/Test3/SerialCommunication.py &
/usr/bin/python2 /home/pi/Test3/serial_data_logger.py &
/usr/bin/python2 /home/pi/Test3/TLChronosProMAIN_391.py &
/usr/bin/python2 /home/pi/Test3/network_info.py &
/usr/bin/python2 /home/pi/Test3/thingsboard_mqtt_publisher.py &
/usr/bin/python2 /home/pi/Test3/xml_parsing_9l.py &
wait



