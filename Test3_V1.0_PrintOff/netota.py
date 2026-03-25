import subprocess
import time
import schedule  # Import schedule

def execute_commands():
    
    subprocess.call(["sudo", "pon", "c16qs"])
    time.sleep(20)
    subprocess.check_call(["python", "/home/pi/Test3/ota2.py"])
    time.sleep(10)  # Wait for 10 seconds
    subprocess.call(["sudo", "poff", "c16qs"])
    time.sleep(5)
    subprocess.call(["sudo", "reboot"])

if __name__ == "__main__":
#    execute_commands()
    
    # Schedule the task for every Sunday at 12 PM
    schedule.every().sunday.at("12:00").do(execute_commands)
    
    # Schedule the task for every Sunday at 9:30 AM
    #schedule.every().tuesday.at("09:30").do(execute_commands)

    
    # Continuously run the scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(1)  # Sleep for a short time before checking again