
import subprocess

def install_package(package_name, version=None):
    try:
        if version:
            package = "{}=={}".format(package_name, version)
        else:
            package = package_name
        print("Installing {}...".format(package))
        subprocess.check_call(["sudo", "pip", "install", package])
        print("Successfully installed {}!".format(package))
    except subprocess.CalledProcessError as e:
        print("Failed to install {}. Error: {}".format(package_name, e))

if __name__ == "__main__":
    packages = [
        {"name": "pad4pi", "version": "1.1.5"},
        {"name": "paho-mqtt", "version": None},
        {"name": "hikvisionapi", "version": None}
    ]

    for package in packages:
        install_package(package["name"], package["version"])
