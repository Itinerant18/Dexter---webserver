import subprocess
import os
import re
import sqlite3

class NetworkSettings:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.create_database()

    def create_database(self):
        if not os.path.exists(self.db_file):
            self.conn = sqlite3.connect(self.db_file)
            cursor = self.conn.cursor()
            cursor.execute('''CREATE TABLE Settings (
                                id INTEGER PRIMARY KEY,
                                setting_name TEXT UNIQUE,
                                setting_value TEXT
                            )''')
            self.conn.commit()
        else:
            self.conn = sqlite3.connect(self.db_file)
            self.add_new_fields()

    def add_new_fields(self):
        """Add new settings to the database if they don't exist."""
        default_settings = [
            ("preferred_dns_server", "8.8.8.8"),
            ("alternate_dns_server", "8.8.4.4"),
            ("reset_to_dhcp", "True")
        ]
        try:
            cursor = self.conn.cursor()
            for setting_name, setting_value in default_settings:
                cursor.execute('''INSERT OR IGNORE INTO Settings (setting_name, setting_value)
                                  VALUES (?, ?)''', (setting_name, setting_value))
            self.conn.commit()
        except sqlite3.Error as e:
            print("Error adding new fields: ", e)

    def update_setting(self, setting_name, setting_value):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''INSERT OR REPLACE INTO Settings (setting_name, setting_value)
                              VALUES (?, ?)''', (setting_name, setting_value))
            self.conn.commit()
            print("Setting '{}' updated successfully.".format(setting_name))
        except sqlite3.Error as e:
            print("Error updating setting: ", e)

    def get_setting(self, setting_name):
        try:
            cursor = self.conn.cursor()
            cursor.execute('''SELECT setting_value FROM Settings WHERE setting_name = ?''', (setting_name,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                print("Setting '{}' not found.".format(setting_name))
                return None
        except sqlite3.Error as e:
            print("Error retrieving setting: ", e)
            return None


db_file = "/home/pi/Test3/network_settings.db"
network_settings = NetworkSettings(db_file)

# Get data from individual elements and store them in variables
static_dynamic_enabled = network_settings.get_setting("Enable/Disable Static/dynamic")
ipv4_ipv6_selection = network_settings.get_setting("IPv4/IPv6 Selection")
ip_address = network_settings.get_setting("Set IP Address")
port_number = network_settings.get_setting("Set Port Number")
subnet_mask = network_settings.get_setting("Subnet mask")
gateway = network_settings.get_setting("Gateway")
dns_setup = network_settings.get_setting("DNS Setup")
apn_settings = network_settings.get_setting("APN Settings")

preferred_dns = network_settings.get_setting("preferred_dns_server")
alternate_dns = network_settings.get_setting("alternate_dns_server")
reset_to_dhcp = network_settings.get_setting("reset_to_dhcp")


# Print or use the variables as needed
#print("e-SIM Enable/Disable:", e_sim_enabled)
#print("Network Selection for e-SIM:", network_selection)
#print("Enable/Disable GNSS:", gnss_enabled)
#print("Alert Types (SMS):", alert_types_sms)
#print("Notification Schedule:", notification_schedule)
#print("Enable/Disable for Network LED Status:", led_status_enabled)
#print("Enable/Disable for Wireless LAN:", wireless_lan_enabled)
#print("Enable/Disable IP Module:", ip_module_enabled)
#print("Enable/Disable Static/dynamic:", static_dynamic_enabled)
#print("IPv4/IPv6 Selection:", ipv4_ipv6_selection)
print("Set IP Address:", ip_address)
print("Set Port Number:", port_number)
print("Subnet mask:", subnet_mask)
print("Gateway:", gateway)
print("DNS Setup:", dns_setup)
print("APN Settings:", apn_settings)
print("Preferred dns:", preferred_dns)
print("Alternate dns:", alternate_dns)





def validate_ip(ip):
    """Validate the IP address format."""
    ip_regex = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    return re.match(ip_regex, ip) is not None and all(0 <= int(part) <= 255 for part in ip.split("."))

def configure_ip(ip_address, subnet_mask, gateway):
    interfaces_file = "/etc/network/interfaces.d/eth0-static"

    try:
        # Backup the original interfaces file
        if not os.path.exists(interfaces_file + ".bak"):
            subprocess.call(["sudo", "cp", interfaces_file, interfaces_file + ".bak"])

        # Write the new network configuration
        with open(interfaces_file, "w") as f:
            f.write("\n")
            f.write("\n\n")
            f.write("auto eth0\n")
            f.write("iface eth0 inet static\n")
            f.write("    address {}\n".format(ip_address))
            f.write("    netmask {}\n".format(subnet_mask))
            

        print("IP address configuration updated successfully.")
    except Exception as e:
        print("Failed to configure IP address:", e)

def configure_dns(dns_servers):
    resolv_conf_file = "/etc/resolv.conf"

    try:
        # Backup the original resolv.conf file
        if not os.path.exists(resolv_conf_file + ".bak"):
            subprocess.call(["sudo", "cp", resolv_conf_file, resolv_conf_file + ".bak"])

        # Write the new DNS server configuration
        with open(resolv_conf_file, "w") as f:
            for dns_server in dns_servers:
                f.write("nameserver {}\n".format(dns_server))

        print("DNS server configuration updated successfully.")
    except Exception as e:
        print("Failed to configure DNS server:", e)

def restart_networking():
    try:
        subprocess.call(["sudo", "systemctl", "restart", "networking"])
        print("Networking service restarted successfully.")
    except Exception as e:
        print("Failed to restart networking service:", e)

def main():
    print("Configure Network Settings on Raspberry Pi")
    
    while True:
        #ip_address = raw_input("Enter IP address (e.g., 192.168.1.100): ")
        if validate_ip(ip_address):
            break
        print("Invalid IP address. Please try again.")

    while True:
        #subnet_mask = raw_input("Enter subnet mask (e.g., 255.255.255.0): ")
        if validate_ip(subnet_mask):
            break
        print("Invalid subnet mask. Please try again.")

    while True:
        #gateway = raw_input("Enter default gateway (e.g., 192.168.1.1): ")
        if validate_ip(gateway):
            break
        print("Invalid gateway address. Please try again.")

    while True:
        #preferred_dns = raw_input("Enter Preferred DNS server (e.g., 8.8.8.8): ")
        if validate_ip(preferred_dns):
            break
        print("Invalid DNS server. Please try again.")

    while True:
        #alternate_dns = raw_input("Enter Alternate DNS server (e.g., 8.8.4.4): ")
        if validate_ip(alternate_dns):
            break
        print("Invalid DNS server. Please try again.")

    configure_ip(ip_address, subnet_mask, gateway)
    configure_dns([preferred_dns, alternate_dns])
    restart_networking()

if __name__ == "__main__":
    main()
