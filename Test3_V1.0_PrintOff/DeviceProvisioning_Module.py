import sqlite3
from paho.mqtt.client import Client
from json import dumps, loads



class ModemConfigDatabase:
    def __init__(self, db_file='modem_config.db'):
        self.db_file = db_file
        self.create_database()

    def create_database(self):
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()

            # Create table if it does not exist
            cursor.execute('''CREATE TABLE IF NOT EXISTS modem_parameters (
                                id INTEGER PRIMARY KEY,
                                access_token TEXT,
                                client_id TEXT,
                                user_name TEXT,
                                password TEXT,
                                gsm_modem_mode TEXT,
                                network_type TEXT,
                                device_name TEXT
                            )''')

            # Check if initial data exists
            cursor.execute('SELECT COUNT(*) FROM modem_parameters')
            if cursor.fetchone()[0] == 0:
                # Insert initial data if the table is empty
                cursor.execute('''INSERT INTO modem_parameters 
                                  (access_token, client_id, user_name, password, gsm_modem_mode, network_type, device_name) 
                                  VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                               ('6dNkl093nG4HvksMmYDD', 'pt2gv4dhnol87qgt2lyw', 'qdg6k3nm8quom2u5u4lv', '3thogxnhdanzkje0vuyw', 'esim', 'ethernet', 'Dexter-HMS'))

            conn.commit()
        except sqlite3.Error as e:
            print("Error creating database: {}".format(e))
        finally:
            if conn:
                conn.close()

    def get_parameter(self, param):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('SELECT {} FROM modem_parameters WHERE id = 1'.format(param))
            value = cursor.fetchone()[0]
            return value
        except sqlite3.Error as e:
            print("Error retrieving parameter {}: {}".format(param, e))
            return None
        finally:
            if conn:
                conn.close()

    def update_parameter(self, param, value):
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute('UPDATE modem_parameters SET {} = ? WHERE id = 1'.format(param), (value,))
            conn.commit()
        except sqlite3.Error as e:
            print("Error updating parameter {} to {}: {}".format(param, value, e))
        finally:
            if conn:
                conn.close()



PROVISION_REQUEST_TOPIC = "/provision/request"
PROVISION_RESPONSE_TOPIC = "/provision/response"

modem_config_db = ModemConfigDatabase()

#device_name = modem_config_db.get_parameter("device_name")
#clientId = modem_config_db.get_parameter("client_id")
#username = modem_config_db.get_parameter("user_name")
#password = modem_config_db.get_parameter("password")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(PROVISION_RESPONSE_TOPIC)
        provision_request = dumps(userdata["provision_request"])
        #print(f"Sending Provision Request: {provision_request}")
        print "Sending Provision Request: {}".format(provision_request)
        client.publish(PROVISION_REQUEST_TOPIC, provision_request)
    else:
        client.disconnect()

def on_message(client, userdata, msg):
    decoded_payload = msg.payload.decode("UTF-8")
    decoded_message = loads(decoded_payload)
    provision_status = decoded_message.get("status")

    if provision_status == "SUCCESS":
        credentials = decoded_message["credentialsValue"]
        #print("Provisioning successful!")
        print "Provisioning successful!"
        #print(f"Provisioned Credentials: {credentials}")
        print "Provisioned Credentials: {}".format(credentials)
        
        # Update the database with the provisioned credentials
        if "clientId" in credentials:
            modem_config_db.update_parameter("client_id", credentials["clientId"])
        if "userName" in credentials:
            modem_config_db.update_parameter("user_name", credentials["userName"])
        if "password" in credentials:
            modem_config_db.update_parameter("password", credentials["password"])
        
    else:
        #print(f"Provisioning failed: {decoded_message.get('errorMsg')}")
        print "Provisioning failed:{}".format(decoded_message.get('errorMsg'))

    client.disconnect()

def provision_device(host, port, provision_request):
    client = Client(userdata={"provision_request": provision_request})
    client.username_pw_set("provision")  
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(host, port, 60)
    client.loop_forever()

def form_basic():
    
    device_name = modem_config_db.get_parameter("device_name")
    clientId = modem_config_db.get_parameter("client_id")
    username = modem_config_db.get_parameter("user_name")
    password = modem_config_db.get_parameter("password")
        
    config = {
        "host":  "thingsboard.cloud",
        "port": 1883,
        "provision_device_key": "abcd",
        "provision_device_secret": "efgh",
#        "device_name": input("Enter Device Name (optional): ").strip(),
#        "clientId": input("Enter Client ID: "),
#        "username": input("Enter MQTT Username: "),
#        "password": input("Enter MQTT Password: "),
        "device_name": device_name,  # Fetched from DB
        "clientId": clientId,  # Fetched from DB
        "username": username,  # Fetched from DB
        "password": password,  # Fetched from DB
    }

    provision_request = {
        "provisionDeviceKey": config["provision_device_key"],
        "provisionDeviceSecret": config["provision_device_secret"],
        "credentialsType": "MQTT_BASIC",
        "username": config["username"],
        "password": config["password"],
        "clientId": config["clientId"],
    }

    if config["device_name"]:
        provision_request["deviceName"] = config["device_name"]

    provision_device(config["host"], config["port"], provision_request)

if __name__ == "__main__":
    form_basic()
