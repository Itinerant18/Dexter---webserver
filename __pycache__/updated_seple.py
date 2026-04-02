# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, session, url_for, redirect
import sqlite3
from sqlite3 import Error
import os
import sys
# from main2 import led_states, toggle_led, cleanup, setup_gpio
from datetime import timedelta
import threading
#sys.path.append('/home/pi/Test3')
#from TLChronosProMAIN_391 import clearLogsFromDB
import psutil
import time
import socket
import logging
import os.path
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# setup_gpio()


app = Flask(__name__)
app.secret_key = "SEPLe"  # set secret key for session
#site_info_file = "site_info.txt"  # Text file to store site information
#password_file = "C:\\Users\\SEPLe-Admin\\Downloads\\Test-3\\password_info.txt"  # Full path to password file
db_file = "sepleDB.db"

# File paths for brand and branch files
BRAND_FILE = "/home/pi/TLChronosPro/Brand.txt"
BRANCH_FILE = "/home/pi/TLChronosPro/Branch.txt"
BRAND_ADDRESS_FILE = "/home/pi/TLChronosPro/brandNameAddress.txt"
BRANCH_ADDRESS_FILE = "/home/pi/TLChronosPro/branchNameAddress.txt"

# In-memory state for synchronization
file_state = {
    "brand_hash": None,
    "branch_hash": None,
    "last_updated_by": None,  # 'web' or 'file'
    "sync_lock": threading.Lock()
}

hostname = socket.gethostname()


def create_connection(db_file):
    conn = None
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, db_file)
        conn = sqlite3.connect(db_path)
        return conn
    except:
        return None


@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)


def get_uptime():
     return time.time() - psutil.boot_time()


@app.route('/home')
def home():
    if 'username' in session:
        db = create_connection('sepleDB.db')
        cursor = db.cursor()
        cursor.execute("SELECT username FROM users ")
        user_data = cursor.fetchone()
        cursor.close()
        db.close()

        db2 = create_connection('/home/pi/Test3/dexterpanel2.db')
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM systemLogs")
        logss_data = cursor2.fetchall()
        cursor2.close()
        db2.close()

        db3 = create_connection('modem_config.db')
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM modem_parameters")
        token_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('landing.html', logg=logss_data, user=user_data, tokenData=token_data)
    return redirect(url_for('login'))
    
def get_cpu_freq():
    freq = psutil.cpu_freq()
    return freq.current

def get_ip_address():
    interfaces = psutil.net_if_addrs()
    for name, addrs in interfaces.items():
        for addr in addrs:
            if addr.family.name == 'AF_INET' and not addr.address.startswith('127.'):
                return addr.address
    return "Not connected"


@app.route('/stats')
def stats():
     data = {
         'cpu': psutil.cpu_percent(interval=1),
         'memory_used': (psutil.virtual_memory().used / psutil.virtual_memory().total) * 100,
         #'memory_used': psutil.virtual_memory().used / (1024 * 1024),  # in MB
         'disk_used': (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100,
         # 'disk_used': psutil.disk_usage('/').used / (1024 * 1024 * 1024),  # in GB
         'bytes_sent': psutil.net_io_counters().bytes_sent / (1024 * 1024),  # in MB
         'bytes_recv': psutil.net_io_counters().bytes_recv / (1024 * 1024),  # in MB
         'uptime': int(get_uptime()),  # in seconds
         'cpu_temp': psutil.sensors_temperatures().get('cpu-thermal', psutil.sensors_temperatures().get('cpu_thermal', [None]))[0].current if psutil.sensors_temperatures().get('cpu-thermal', psutil.sensors_temperatures().get('cpu_thermal')) else None,
         'freq': get_cpu_freq(),
         'network_interfaces': get_ip_address()
     }
     return jsonify(data)




@app.route('/')
def index():
    return render_template('index.html')


@app.route('/delete')
def clear_logs():
    
    connection = sqlite3.connect("/home/pi/Test3/dexterpanel2.db")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM systemLogs")
    connection.commit()
    connection.close()
    return redirect(url_for('logs'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = create_connection(db_file)
        if db is None:
            return "Failed to connect to database"

        cursor = db.cursor()
        try:
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user_data = cursor.fetchone()
            cursor.close()
            db.close()
            if user_data:
                session['username'] = username
                return redirect(url_for('home'))
            else:
                return render_template('index.html', alert_userpass=True)
        except:
            return None

    return render_template('index.html')


@app.route('/resetpassword', methods=['GET', 'POST'])
def resetpassword():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        npassword = request.form['newpassword']
        cpassword = request.form['cpassword']

        db = create_connection(db_file)
        if db is None:
            return "Failed to connect to database"

        cursor = db.cursor()
        try:
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?", (username, password))
            existing_user = cursor.fetchone()
            if existing_user:
                if npassword == cpassword:
                    cursor.execute(
                        "UPDATE users SET password=? WHERE username=?", (npassword, username))
                    db.commit()
                    cursor.close()
                    db.close()
                    return render_template('index.html', reset_password=True)
                else:
                    return render_template('reset.html', not_same=True)
            else:
                return render_template('reset.html', wrong_password=True)
        except Error as e:
            # print("Error executing SQL query:", e)
            return "Error executing SQL query"

    return render_template('reset.html')


def restart_server():
    """Re-execute the current script (simulate restart)."""
    python = sys.executable
    os.execl(python, python, *sys.argv)


def session_clear():
    session.pop('username', None)


def reboot_rpi():
    os.system("sudo /sbin/reboot")

@app.route('/restart', methods=['POST'])
def restart():
    session_clear()
    threading.Timer(10.0, reboot_rpi).start()
    return 'Rebooting...'


@app.route('/terminate', methods=['POST', 'GET'])
def terminate():
    session_clear()
    threading.Timer(1.0, lambda: terminate_server()).start()
    return render_template('index.html', poweroff=True)


def terminate_server():
    """Terminate the Flask application."""
    os._exit(0)


@app.route('/device_config')
def device_config():
    if 'username' in session:
        username = session['username']
        db = create_connection(db_file)
        if db:
            try:
                cursor = db.cursor()
                cursor.execute(
                    "SELECT * FROM users WHERE username=?", (username,))
                user_data = cursor.fetchone()
                cursor.close()
                db.close()

                db3 = create_connection("dexterpanel2.db")
                cursor3 = db3.cursor()
                cursor3.execute("SELECT * FROM systemLogs ")
                logss_data = cursor3.fetchall()
                cursor3.close()
                db3.close()
                return render_template('device_config.html', logg=logss_data, user=user_data)
            except:
                return redirect(url_for('login'))
    return redirect(url_for('login'))


@app.route('/get_zone', methods=['GET', 'PUT'])
def get_zone():
    try:
        # Read from the Raspberry Pi file path
        file_path = "/home/pi/TLChronosPro/zoneSettings.txt"
        with open(file_path, "r") as file:
            lines = file.readlines()
            zones_data = []
            for i, line in enumerate(lines):
                if line.strip():  # Skip empty lines
                    activated, buzzer, device = map(int, line.strip().split())
                    # Convert numeric values to what frontend expects
                    device_name = None
                    if device == 1:
                        device_name = "BAS"
                    elif device == 2:
                        device_name = "FAS"
                    elif device == 3:
                        device_name = "Time Lock"
                    elif device == 4:
                        device_name = "BACS"
                    elif device == 5:
                        device_name = "CCTV"
                    elif device == 6:
                        device_name = "IAS"

                    buzzer_status = "on" if buzzer == 1 else "off"
                    zones_data.append(
                        [i+1, activated, device_name, buzzer_status])

            return jsonify(zones_data)
    except:
        # If file read fails, try database as fallback
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM zone")
            zones_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(zones_data)
        return jsonify([])


def read_zone_file(file_path):
    try:
        with open(file_path, "r") as file:
            return [line.strip() for line in file.readlines()]
    except:
        return []


def log_file_change(file_type):
    try:
        db = create_connection("dexterpanel2.db")
        if db:
            cursor = db.cursor()
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            message = "%s file updated" % file_type
            cursor.execute("INSERT INTO systemLogs (date, message) VALUES (?, ?)",
                           (timestamp, message))
            db.commit()
            cursor.close()
            db.close()
    except:
        pass


@app.route('/update_zone', methods=['PUT'])
def update_zone():
    if request.method == 'PUT':
        data = request.json
        if not data:
            return redirect(url_for('device_config'))

        try:
            # Set the correct Raspberry Pi file path
            file_path = "/home/pi/TLChronosPro/zoneSettings.txt"

            # Read existing lines from zoneSettings.txt
            lines = ["0 0 0" for _ in range(16)]  # Initialize with defaults
            try:
                with open(file_path, "r") as file:
                    file_lines = file.readlines()
                    for i, line in enumerate(file_lines):
                        if i < 16:  # Only process up to 16 lines
                            lines[i] = line.strip()
            except:
                pass

            # Update database and text file
            db = create_connection(db_file)
            if db:
                cursor = db.cursor()
                try:
                    for zone_data in data:
                        zoneId = zone_data.get('zoneId')
                        if not zoneId or not isinstance(zoneId, int):
                            continue

                        activated = zone_data.get('activated', 0)
                        selectedDevice = zone_data.get('selectedDevice', '')
                        buzzerStatus = zone_data.get('buzzerStatus', 'off')

                        if 1 <= zoneId <= 16:  # Validate zone ID
                            # Update database
                            cursor.execute(
                                "SELECT * FROM zone WHERE zoneId=?", (zoneId,))
                            existing_zone = cursor.fetchone()

                            if existing_zone:
                                cursor.execute("UPDATE zone SET activated=?, selectedDevice=?, buzzerStatus=? WHERE zoneId=?",
                                               (activated, selectedDevice, buzzerStatus, zoneId))
                            else:
                                cursor.execute("INSERT INTO zone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, ?, ?, ?)",
                                               (zoneId, activated, selectedDevice, buzzerStatus))

                            # Convert values for text file
                            device_num = 0
                            if selectedDevice == "BAS":
                                device_num = 1
                            elif selectedDevice == "FAS":
                                device_num = 2
                            elif selectedDevice == "Time Lock":
                                device_num = 3
                            elif selectedDevice == "BACS":
                                device_num = 4
                            elif selectedDevice == "CCTV":
                                device_num = 5
                            elif selectedDevice == "IAS":
                                device_num = 6

                            buzzer_num = 1 if buzzerStatus == "on" else 0

                            # Update the corresponding line in the text file
                            lines[zoneId -
                                  1] = "%d %d %d" % (activated, buzzer_num, device_num)

                    # Write all updates to zoneSettings.txt
                    try:
                        # Create directory if it doesn't exist
                        directory = os.path.dirname(file_path)
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                        with open(file_path, "w") as file:
                            file.write("\n".join(lines) + "\n")
                    except Exception as e:
                        logging.error(
                            "Error writing to zoneSettings.txt: {}".format(e))
                        # Still continue with database update even if file write fails

                    # Log the change
                    log_file_change("Zone")

                    db.commit()
                    cursor.close()
                    db.close()
                    return jsonify({'Message': 'Done'})
                except:
                    if cursor:
                        cursor.close()
                    if db:
                        db.close()
                    return redirect(url_for('device_config'))
        except:
            return redirect(url_for('device_config'))
    return redirect(url_for('device_config'))


@app.route('/powerzone_config')
def powerzone_config():
    if 'username' in session:
        username = session['username']
        db = create_connection(db_file)
        if db:
            try:
                cursor = db.cursor()
                cursor.execute(
                    "SELECT * FROM users WHERE username=?", (username,))
                user_data = cursor.fetchone()
                cursor.close()
                db.close()
                db3 = create_connection("dexterpanel2.db")
                cursor3 = db3.cursor()
                cursor3.execute("SELECT * FROM systemLogs ")
                logss_data = cursor3.fetchall()
                cursor3.close()
                db3.close()
                return render_template('powerzone_config.html', logg=logss_data, user=user_data)
            except Error as e:
                # print(f"Database query error: {e}")
                return redirect(url_for('login'))
    return redirect(url_for('login'))


# Get power zone data route
@app.route('/get_powerzone', methods=['GET', 'PUT'])
def get_powerzone():
    if 'username' in session:
        try:
            # Read from the Raspberry Pi file path
            file_path = "/home/pi/TLChronosPro/powerZoneSettings.txt"
            with open(file_path, "r") as file:
                lines = file.readlines()
                zones_data = []
                for i, line in enumerate(lines):
                    if i < 8 and line.strip():  # Only process first 8 lines for power zones
                        activated, buzzer, device = map(
                            int, line.strip().split())
                        # Convert numeric values to what frontend expects
                        device_name = None
                        if device == 1:
                            device_name = "BAS"
                        elif device == 2:
                            device_name = "FAS"
                        elif device == 3:
                            device_name = "Time Lock"
                        elif device == 4:
                            device_name = "BACS"
                        elif device == 5:
                            device_name = "NVR & DVR"
                        elif device == 6:
                            device_name = "IAS"

                        buzzer_status = "on" if buzzer == 1 else "off"
                        zones_data.append(
                            [i+1, activated, device_name, buzzer_status])

                return jsonify(zones_data)
        except:
            # If file read fails, try database as fallback
            db = create_connection(db_file)
            if db:
                cursor = db.cursor()
                cursor.execute("SELECT * FROM powerzone")
                zones_data = cursor.fetchall()
                cursor.close()
                db.close()
                return jsonify(zones_data)
            return jsonify([])
    return redirect(url_for('login'))


# Update power zone route
@app.route('/update_powerzone', methods=['PUT'])
def update_powerzone():
    if request.method == 'PUT':
        data = request.json
        if not data:
            return redirect(url_for('powerzone_config'))

        try:
            # Set the correct Raspberry Pi file path
            file_path = "/home/pi/TLChronosPro/powerZoneSettings.txt"

            # Initialize 16 lines - first 8 for power zones, next 8 with zeros
            lines = ["0 0 0" for _ in range(16)]

            # Read existing lines from powerZoneSettings.txt
            try:
                with open(file_path, "r") as file:
                    file_lines = file.readlines()
                    for i, line in enumerate(file_lines):
                        if i < 16:  # Only process up to 16 lines
                            lines[i] = line.strip()
            except:
                pass

            # Update database and text file
            db = create_connection(db_file)
            if db:
                cursor = db.cursor()
                try:
                    # First update the power zones (first 8)
                    for zone_data in data:
                        zoneId = zone_data.get('zoneId')
                        if not zoneId or not isinstance(zoneId, int):
                            continue

                        activated = zone_data.get('activated', 0)
                        selectedDevice = zone_data.get('selectedDevice', '')
                        buzzerStatus = zone_data.get('buzzerStatus', 'off')

                        if 1 <= zoneId <= 8:  # Only process first 8 zones for power zones
                            # Update database
                            cursor.execute(
                                "SELECT * FROM powerzone WHERE zoneId=?", (zoneId,))
                            existing_zone = cursor.fetchone()
                            if existing_zone:
                                cursor.execute("UPDATE powerzone SET activated=?, selectedDevice=?, buzzerStatus=? WHERE zoneId=?",
                                               (activated, selectedDevice, buzzerStatus, zoneId))
                            else:
                                cursor.execute("INSERT INTO powerzone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, ?, ?, ?)",
                                               (zoneId, activated, selectedDevice, buzzerStatus))

                            # Convert values for text file
                            device_num = 0
                            if selectedDevice == "BAS":
                                device_num = 1
                            elif selectedDevice == "FAS":
                                device_num = 2
                            elif selectedDevice == "Time Lock":
                                device_num = 3
                            elif selectedDevice == "BACS":
                                device_num = 4
                            elif selectedDevice == "NVR & DVR":
                                device_num = 5
                            elif selectedDevice == "IAS":
                                device_num = 6

                            buzzer_num = 1 if buzzerStatus == "on" else 0

                            # Update the corresponding line in the text file
                            lines[zoneId -
                                  1] = "%d %d %d" % (activated, buzzer_num, device_num)

                    # Ensure next 8 zones are zeros in both database and text file
                    for zoneId in range(9, 17):
                        # Update database for zones 9-16 with zeros
                        cursor.execute(
                            "SELECT * FROM powerzone WHERE zoneId=?", (zoneId,))
                        existing_zone = cursor.fetchone()
                        if existing_zone:
                            cursor.execute("UPDATE powerzone SET activated=0, selectedDevice='', buzzerStatus='off' WHERE zoneId=?",
                                           (zoneId,))
                        else:
                            cursor.execute("INSERT INTO powerzone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, 0, '', 'off')",
                                           (zoneId,))

                        # Ensure text file lines 9-16 are zeros
                        lines[zoneId - 1] = "0 0 0"

                    # Write all updates to powerZoneSettings.txt
                    try:
                        # Create directory if it doesn't exist
                        directory = os.path.dirname(file_path)
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                        with open(file_path, "w") as file:
                            file.write("\n".join(lines) + "\n")
                    except Exception as e:
                        logging.error(
                            "Error writing to powerZoneSettings.txt: {}".format(e))
                        # Still continue with database update even if file write fails

                    # Log the change
                    log_file_change("Power Zone")

                    db.commit()
                    cursor.close()
                    db.close()
                    return jsonify({'Message': 'Done'})
                except:
                    if cursor:
                        cursor.close()
                    if db:
                        db.close()
                    return redirect(url_for('powerzone_config'))
        except:
            return redirect(url_for('powerzone_config'))
    return redirect(url_for('powerzone_config'))


@app.route('/advanced')
def advanced():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('advanced.html', logg=logss_data, user=user_data)
    return redirect(url_for('login'))

# Enhanced file handling functions for two-way synchronization
def safe_read(file_path):
    """Safely read a file and return its content."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return f.read()
        return ""
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return ""

def safe_write(file_path, content):
    """Safely write content to a file."""
    try:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        logging.error(f"Error writing to file {file_path}: {e}")
        return False

def calculate_file_hash(file_path):
    """Calculate a hash of file content for change detection."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()
                return hashlib.md5(content.encode()).hexdigest()
        return None
    except Exception as e:
        logging.error(f"Error calculating hash for {file_path}: {e}")
        return None

def extract_name_from_file(file_content):
    """Extract the actual name from the formatted file content."""
    if not file_content:
        return ""
    lines = file_content.strip().split('\n')
    if not lines:
        return ""
    
    # Extract the first line and remove padding
    first_line = lines[0].strip()
    # Remove plus signs and spaces, then strip again
    name = first_line.replace('+', '').strip()
    return name

def create_zeroes_lines(width=16, num_lines=7):
    """Create the lines of zeroes for the file format."""
    return '\n'.join(['0 ' * (width // 2) for _ in range(num_lines)])

# File system event handler for monitoring changes to Brand.txt and Branch.txt
class FileChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory:
            # Check if it's one of our target files
            if event.src_path in [BRAND_FILE, BRANCH_FILE]:
                # Avoid processing our own changes
                with file_state["sync_lock"]:
                    if file_state["last_updated_by"] == "web":
                        file_state["last_updated_by"] = None
                        return
                
                # Process the file change
                self.process_file_change(event.src_path)
    
    def process_file_change(self, file_path):
        # Read the file content
        file_content = safe_read(file_path)
        
        # Calculate new hash
        new_hash = calculate_file_hash(file_path)
        
        # Check if this is a real change
        is_brand = file_path == BRAND_FILE
        current_hash = file_state["brand_hash"] if is_brand else file_state["branch_hash"]
        
        if new_hash != current_hash:
            with file_state["sync_lock"]:
                # Update our state
                if is_brand:
                    file_state["brand_hash"] = new_hash
                else:
                    file_state["branch_hash"] = new_hash
                
                file_state["last_updated_by"] = "file"
                
                # Extract the name
                name = extract_name_from_file(file_content)
                
                # Log the change
                log_file_change("Brand" if is_brand else "Branch")
                
                # Update the app config with the new name
                if is_brand:
                    app.config['BRAND_NAME'] = name
                else:
                    app.config['BRANCH_NAME'] = name

# Initialize file monitoring
def init_file_monitoring():
    # Create the files if they don't exist
    if not os.path.exists(BRAND_FILE):
        name_plus_padded = "+" * 16
        zeroes_lines = create_zeroes_lines()
        safe_write(BRAND_FILE, f"{name_plus_padded}\n{zeroes_lines}")
    
    if not os.path.exists(BRANCH_FILE):
        name_plus_padded = "+" * 16
        zeroes_lines = create_zeroes_lines()
        safe_write(BRANCH_FILE, f"{name_plus_padded}\n{zeroes_lines}")
    
    # Initialize file state
    file_state["brand_hash"] = calculate_file_hash(BRAND_FILE)
    file_state["branch_hash"] = calculate_file_hash(BRANCH_FILE)
    
    # Read initial values
    brand_content = safe_read(BRAND_FILE)
    branch_content = safe_read(BRANCH_FILE)
    
    app.config['BRAND_NAME'] = extract_name_from_file(brand_content)
    app.config['BRANCH_NAME'] = extract_name_from_file(branch_content)
    
    # Set up file system observer
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(BRAND_FILE), recursive=False)
    observer.start()
    
    # Register a function to stop the observer when the app shuts down
    import atexit
    atexit.register(lambda: observer.stop())

# Initialize the app
@app.before_first_request
def initialize_app():
    init_file_monitoring()

@app.route('/general')
def general():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor2 = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        cursor2.execute("SELECT * FROM general")
        user_data = cursor.fetchone()
        user_data2 = cursor2.fetchall()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        # Read brand and branch names from files with proper extraction
        brand_content = safe_read(BRAND_FILE)
        branch_content = safe_read(BRANCH_FILE)
        
        brand_name = extract_name_from_file(brand_content)
        branch_name = extract_name_from_file(branch_content)

        return render_template('general.html', brand_name=brand_name, branch_name=branch_name, 
                              user=user_data, logg=logss_data, user2=user_data2)
    return redirect(url_for('login'))

@app.route('/brandname', methods=['POST'])
def brandname():
    if request.method == 'POST':
        brand_name = request.form.get('brandName', '').strip()
        branch_name = request.form.get('siteName', '').strip()

        if not brand_name or not branch_name:
            return "Both brand name and branch name are required.", 400

        if len(brand_name) > 16 or len(branch_name) > 16:
            return "Each input must be 16 characters or fewer.", 400

        with file_state["sync_lock"]:
            file_state["last_updated_by"] = "web"
            
            # Center values
            name_centered = brand_name.center(16)                   # space padded
            address_centered = brand_name.center(16, '+')           # plus padded

            branch_name_centered = branch_name.center(16)           # space padded
            branch_address_centered = branch_name.center(16, '+')   # plus padded

            # Create zeroes lines
            zeroes_lines = create_zeroes_lines()

            # Write to Brand.txt with format
            safe_write(BRAND_FILE, f"{address_centered}\n{zeroes_lines}")
            safe_write(BRAND_ADDRESS_FILE, address_centered)

            # Write to Branch.txt with format
            safe_write(BRANCH_FILE, f"{branch_address_centered}\n{zeroes_lines}")
            safe_write(BRANCH_ADDRESS_FILE, branch_address_centered)

            # Update file state hashes
            file_state["brand_hash"] = calculate_file_hash(BRAND_FILE)
            file_state["branch_hash"] = calculate_file_hash(BRANCH_FILE)
            
            # Update app config
            app.config['BRAND_NAME'] = brand_name
            app.config['BRANCH_NAME'] = branch_name
            
            # Log the change
            log_file_change("Brand and Branch")

        return redirect(url_for('general'))

@app.route('/general_data', methods=['GET', 'POST'])
def general_data():
    if request.method == 'POST':
        success_message = None
        error_message = None
        action = request.form.get('action')

        if action == 'change_password':
            current_password = request.form.get('currentPassword')
            new_password = request.form.get('newPassword')
            confirm_password = request.form.get('confirmPassword')

            if not all([current_password, new_password, confirm_password]):
                error_message = 'All password fields are required'
            elif new_password != confirm_password:
                error_message = 'New passwords do not match'
            else:
                db = create_connection(db_file)
                if db:
                    try:
                        cursor = db.cursor()
                        cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                                       (session['username'], current_password))
                        if cursor.fetchone():
                            cursor.execute("UPDATE users SET password=? WHERE username=?",
                                           (new_password, session['username']))
                            db.commit()
                            success_message = 'Password updated successfully'
                        else:
                            error_message = 'Current password is incorrect'
                    except Exception:
                        error_message = 'Error updating password'
                    finally:
                        cursor.close()
                        db.close()
                else:
                    error_message = 'Database connection failed'

        elif action == 'save_date':
            new_date = request.form.get('setDate')
            if not new_date:
                error_message = 'Please select a date'
            else:
                try:
                    success_message = 'Date updated successfully'
                except Exception:
                    error_message = 'Error updating date'

        else:
            brand_name = request.form.get('brandName')
            site_name = request.form.get('siteName')

            if not all([brand_name, site_name]):
                error_message = 'Both brand name and site name are required'
            else:
                db = create_connection(db_file)
                if db:
                    try:
                        cursor = db.cursor()
                        cursor.execute("SELECT * FROM general WHERE ID=1")
                        existing = cursor.fetchall()
                        if existing:
                            cursor.execute("UPDATE general SET brand_name=?, site_name=? WHERE ID=1",
                                           (brand_name, site_name))
                        else:
                            cursor.execute("INSERT INTO general (brand_name, site_name) VALUES (?,?)",
                                           (brand_name, site_name))
                        db.commit()
                        success_message = 'Brand and site information updated successfully'

                        try:
                            db2 = create_connection("dexterpanel2.db")
                            if db2:
                                cursor2 = db2.cursor()
                                log_message = "General settings updated"
                                cursor2.execute("INSERT INTO systemLogs (date, message) VALUES (datetime('now', 'localtime'), ?)",
                                                (log_message,))
                                db2.commit()
                                cursor2.close()
                                db2.close()
                        except:
                            pass

                    except:
                        error_message = 'Error updating settings'
                    finally:
                        cursor.close()
                        db.close()
                else:
                    error_message = 'Database connection failed'

    return redirect(url_for('general', success_message=success_message, error_message=error_message))


@app.route('/maintenance')
def maintenance():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template('maintenance.html', logg=logss_data, user=user_data)
    return redirect(url_for('login'))


@app.route('/system_test')
def system_test():
    if 'username' in session:
        username = session['username']
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        # Initialize LED states if not exists
        led_states = {
            1: False,  # Lamp Test
            2: False,  # Relay Test
            3: False   # Buzzer Test
        }

        return render_template('systemTest.html', logg=logss_data, user=user_data, led_states=led_states)
    return redirect(url_for('login'))


@app.route('/control', methods=['POST'])
def control():
    if request.method == 'POST':
        try:
            led_id = int(request.form['led'])
            return redirect(url_for('system_test'))
        except:
            return redirect(url_for('system_test'))


@app.route('/logs')
def logs():
    if 'username' in session:
        username = session['username']

        # Connect to the first database (sepleDB.db)
        db1 = create_connection("sepleDB.db")
        cursor1 = db1.cursor()
        cursor1.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor1.fetchone()
        cursor1.close()
        db1.close()

        # Connect to the second database (dexterpanel2.db)
        db2 = create_connection("/home/pi/Test3/dexterpanel2.db")
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM systemLogs")
        logs_data = cursor2.fetchall()
        cursor2.close()
        db2.close()

        # Return the logs data in reverse order (newest first)
        logs_data = list(reversed(logs_data))

        # Get additional data
        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        return render_template('logs.html', logs=logs_data, logg=logss_data, user=user_data)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
