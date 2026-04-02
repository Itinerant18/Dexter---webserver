import subprocess

def get_ip_address():
    """
    Retrieves the IP address of the LAN interface.

    Returns:
        str: The IP address or 'N/A' if not found.
    """
    try:
        ifconfig_output = subprocess.check_output(['ifconfig', 'eth0'], stderr=subprocess.STDOUT)
        for line in ifconfig_output.splitlines():
            if 'inet ' in line:
                return line.split()[1]
    except subprocess.CalledProcessError:
        pass
    return 'N/A'

def get_mac_address():
    """
    Retrieves the MAC address of the LAN interface.

    Returns:
        str: The MAC address or 'N/A' if not found.
    """
    try:
        ifconfig_output = subprocess.check_output(['ifconfig', 'eth0'], stderr=subprocess.STDOUT)
        for line in ifconfig_output.splitlines():
            if 'ether ' in line:
                return line.split()[1]
    except subprocess.CalledProcessError:
        pass
    return 'N/A'

def get_default_gateway():
    """
    Retrieves the default gateway.

    Returns:
        str: The default gateway or 'N/A' if not found.
    """
    try:
        route_output = subprocess.check_output(['ip', 'route', 'show'], stderr=subprocess.STDOUT)
        for line in route_output.splitlines():
            if 'default via' in line:
                return line.split()[2]
    except subprocess.CalledProcessError:
        pass
    return 'N/A'

def get_dns_servers():
    """
    Retrieves the DNS servers.

    Returns:
        list: A list of DNS server addresses or ['N/A'] if none are found.
    """
    try:
        dns_servers = []
        with open('/etc/resolv.conf', 'r') as resolv_file:
            for line in resolv_file:
                if line.startswith('nameserver'):
                    dns_servers.append(line.split()[1])
        if dns_servers:
            return dns_servers
    except IOError:
        pass
    return ['N/A']

# Example usage
if __name__ == "__main__":
    print("IP Address:", get_ip_address())
    print("MAC Address:", get_mac_address())
    print("Default Gateway:", get_default_gateway())
    print("DNS Servers:", get_dns_servers())
