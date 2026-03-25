import os
import subprocess

def reset_to_dhcp():
#    interfaces_file = "/etc/network/interfaces"
    interfaces_file = "/etc/network/interfaces.d/eth0-static"  # for OTA update
    interfaces_backup = interfaces_file + ".bak"

    try:
        # Backup the existing interfaces file
        if not os.path.exists(interfaces_backup):
            subprocess.call(["sudo", "cp", interfaces_file, interfaces_backup])

        # Write new DHCP configuration
        with open(interfaces_file, "w") as f:
            f.write("auto lo\n")
            f.write("iface lo inet loopback\n\n")
            f.write("auto eth0\n")
            f.write("iface eth0 inet dhcp\n")

        print("Network configuration reset to DHCP successfully.")
    except Exception as e:
        print("Failed to reset network configuration:", e)

def restart_networking():
    try:
        # Restart networking service
        subprocess.call(["sudo", "systemctl", "restart", "networking"])
        print("Networking service restarted successfully.")
    except Exception as e:
        print("Failed to restart networking service:", e)

def reset_dhcp():
    print("Resetting network configuration to DHCP...")
    reset_to_dhcp()
    restart_networking()

    # Verify the configuration
    print("\nVerifying new network configuration...")
    subprocess.call(["ip", "addr", "show", "eth0"])

if __name__ == "__main__":
    reset_dhcp()
