import os
import sys
import subprocess
import time
import paho.mqtt.client as mqtt
from time import sleep
import json
from hashlib import sha256, sha384, sha512, md5
from zlib import crc32
import mmh3
from math import ceil
from threading import Thread

# ThingsBoard attributes
SW_CHECKSUM_ATTR = "sw_checksum"
SW_CHECKSUM_ALG_ATTR = "sw_checksum_algorithm"
SW_SIZE_ATTR = "sw_size"
SW_TITLE_ATTR = "sw_title"
SW_VERSION_ATTR = "sw_version"
SW_STATE_ATTR = "sw_state"
REQUIRED_SHARED_KEYS = "%s,%s,%s,%s,%s" % (SW_CHECKSUM_ATTR, SW_CHECKSUM_ALG_ATTR, SW_SIZE_ATTR, SW_TITLE_ATTR, SW_VERSION_ATTR)

# Configuration
def collect_required_data():
    return {
        "host": "thingsboard.cloud",
        "port": 1883,
        "token": "98M56S2rrGaJVZwBMGsS",
        "chunk_size": 0
    }

# Checksum verification
def verify_checksum(data, algorithm, expected_checksum):
    if data is None or expected_checksum is None:
        print "Missing data or checksum!"
        return False
    
    checksum_map = {
        "sha256": lambda d: sha256(d).hexdigest(),
        "sha384": lambda d: sha384(d).hexdigest(),
        "sha512": lambda d: sha512(d).hexdigest(),
        "md5": lambda d: md5(d).hexdigest(),
        "murmur3_32": lambda d: '%08x' % mmh3.hash(d, signed=False),
        "murmur3_128": lambda d: '%032x' % mmh3.hash128(d, signed=False),
        "crc32": lambda d: '%08x' % (crc32(d) & 0xffffffff)
    }
    
    computed_checksum = checksum_map.get(algorithm.lower())
    if not computed_checksum:
        print "Unsupported checksum algorithm."
        return False
    
    return computed_checksum(data) == expected_checksum

class SoftwareClient(mqtt.Client):
    def __init__(self, chunk_size=0):
        mqtt.Client.__init__(self)
        self.on_connect = self.__on_connect
        self.on_message = self.__on_message
        self.chunk_size = chunk_size
        self.software_data = b''
        self.software_info = {}
        self.software_received = False
        self.software_path = "/home/pi/Test3/TLChronosProMAIN_391.py"

    def __on_connect(self, client, userdata, flags, rc):
        print "Connected to ThingsBoard"
        self.subscribe("v1/devices/me/attributes/response/+")
        self.subscribe("v1/devices/me/attributes")
        self.subscribe("v2/sw/response/+/chunk/+")
        self.request_software_info()

    def __on_message(self, client, userdata, msg):
        if msg.topic.startswith("v1/devices/me/attributes"):
            self.software_info = json.loads(msg.payload).get("shared", {})
            self.download_software()
        elif msg.topic.startswith("v2/sw/response/"):
            self.software_data += msg.payload
            if len(self.software_data) == self.software_info[SW_SIZE_ATTR]:
                self.process_software()
            else:
                self.request_next_chunk()
    
    def request_software_info(self):
        self.publish("v1/devices/me/attributes/request/1", json.dumps({"sharedKeys": REQUIRED_SHARED_KEYS}))
    
    def download_software(self):
        if self.software_info.get(SW_VERSION_ATTR) != "current_version":
            print "New software available, starting download..."
            self.software_data = b''
            self.request_next_chunk()
    
    def request_next_chunk(self):
        self.publish("v2/sw/request/1/chunk/0", b"")
    
    def process_software(self):
        if verify_checksum(self.software_data, self.software_info[SW_CHECKSUM_ALG_ATTR], self.software_info[SW_CHECKSUM_ATTR]):
            print "Checksum verified, applying update..."
            with open(self.software_path, "wb") as f:
                f.write(self.software_data)
            self.apply_update()
        else:
            print "Checksum verification failed, update aborted."
    
    def apply_update(self):
        print "Applying update and exiting..."
        time.sleep(10)
        sys.exit(0)

if __name__ == '__main__':
    config = collect_required_data()
    client = SoftwareClient(config["chunk_size"])
    client.username_pw_set(config["token"])
    client.connect(config["host"], config["port"])
    client.loop_forever()
