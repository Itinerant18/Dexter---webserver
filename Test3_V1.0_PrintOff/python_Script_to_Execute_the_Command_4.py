import subprocess

try:
    # Command to be executed
    command = ['sudo', '/usr/bin/python2', '/home/pi/Test3/Configure_Network_7.py']

    # Execute the command
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    # Check for errors
    if process.returncode == 0:
        print("Output:")
        print(stdout)
    else:
        print("Errors:")
        print(stderr)

except Exception as e:
    print("An error occurred:")
    print(str(e))
