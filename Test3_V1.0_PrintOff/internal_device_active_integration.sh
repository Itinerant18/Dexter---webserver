#!/bin/bash
/usr/bin/python2 /home/pi/Test3/xml_parsing_9.py &
/usr/bin/python2 /home/pi/Test3/hikvision1_biometric_14.py &
/usr/bin/python2 /home/pi/Test3/dahua_nvr_dvr_get_store_json_7i.py &
/usr/bin/python2 /home/pi/Test3/Extract_Logs_Dahua_41.py &
/usr/bin/python2 /home/pi/Test3/Dahua_Recording_SD_Card_Cam_Info_Status_int.py &
/usr/bin/python2 /home/pi/Test3/Hik_SD_Card_REC_Cam_Info_Status_int.py &
/usr/bin/python2 /home/pi/Test3/netota.py &
/usr/bin/python2 /home/pi/Test3/hik_RTC_sync.py &
/usr/bin/python2 /home/pi/Test3/dahua_RTC_sync.py &
wait

