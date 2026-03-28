# -*- coding: utf-8 -*-
import os
import sys
import socket
import logging
import os.path
import json
import sqlite3
import time
import threading
from sqlite3 import Error
from datetime import datetime, timedelta

from flask import (
    Flask,
    flash,
    render_template,
    request,
    jsonify,
    session,
    url_for,
    redirect
)

import psutil

sys.path.append('/home/pi/Test3')
from Lan_setting import resetDHCP, configureStaticNetwork, device_provisioning

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "SEPLe"  # set secret key for session
password_file = "/home/pi/TLChronosPro/AdminPass.txt"  # Full path to password file
db_file = "sepleDB.db"

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
    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
    )
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)


def get_uptime():
    return time.time() - psutil.boot_time()


def check_user_access(required_permissions=None):
    """Check if user has required permissions for specific pages"""
    if "username" not in session:
        return False
    
    user_type = session.get("user_type", "user")
    
    # Site engineers have access to everything
    if user_type == "site_engineer":
        return True
    
    # Regular users have restricted access
    if user_type == "user":
        # Define restricted pages that users cannot access
        restricted_pages = [
            "provision",      # Device Provisioning
            "lan",            # LAN setup  
            "device_credential"  # Device credentials
        ]
        
        if required_permissions in restricted_pages:
            return False
        return True
    
    return False


@app.route("/home")
def home():
    if "username" in session:
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT username FROM users ")
        user_data = cursor.fetchone()
        cursor.close()
        db.close()

        db2 = create_connection("/home/pi/Test3/dexterpanel2.db")
        db3 = create_connection("/home/pi/Test3/securelink.db")
        cursor3 = db3.cursor()
        cursor3.execute("Select batch_number from device_info")
        deviceinfo = cursor3.fetchone()
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM systemLogs")
        logss_data = cursor2.fetchall()
        cursor2.close()
        db2.close()

        db3 = create_connection("modem_config.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM modem_parameters")
        token_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template(
            "landing.html", logg=logss_data, user=user_data, tokenData=token_data,deviceinfo = deviceinfo
        )
    return redirect(url_for("login"))


def get_cpu_freq():
    freq = psutil.cpu_freq()
    return freq.current


def get_ip_address():
    # interfaces = psutil.net_if_addrs()
    # for name, addrs in interfaces.items():
    # for addr in addrs:
    # print(addr)
    # if addr.family.name == 'AF_INET' and not addr.address.startswith('127.'):
    # return addr.address
    return "Not connected"


@app.route("/stats")
def stats():
    data = {
        "cpu": psutil.cpu_percent(interval=1),
        "memory_used": (psutil.virtual_memory().used / psutil.virtual_memory().total)
        * 100,
        #'memory_used': psutil.virtual_memory().used / (1024 * 1024),  # in MB
        "disk_used": (psutil.disk_usage("/").used / psutil.disk_usage("/").total) * 100,
        # 'disk_used': psutil.disk_usage('/').used / (1024 * 1024 * 1024),  # in GB
        "bytes_sent": psutil.net_io_counters().bytes_sent / (1024 * 1024),  # in MB
        "bytes_recv": psutil.net_io_counters().bytes_recv / (1024 * 1024),  # in MB
        "uptime": int(get_uptime()),  # in seconds
        "cpu_temp": (
            psutil.sensors_temperatures()
            .get(
                "cpu-thermal", psutil.sensors_temperatures().get("cpu_thermal", [None])
            )[0]
            .current
            if psutil.sensors_temperatures().get(
                "cpu-thermal", psutil.sensors_temperatures().get("cpu_thermal")
            )
            else None
        ),
        "freq": get_cpu_freq(),
        "network_interfaces": get_ip_address(),
    }
    print(jsonify(data))
    return jsonify(data)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/financial")
def financial():
    return render_template("financial.html")


@app.route("/delete")
def clear_logs():

    connection = sqlite3.connect("/home/pi/Test3/dexterpanel2.db")
    cursor = connection.cursor()
    cursor.execute("DELETE FROM systemLogs")
    connection.commit()
    connection.close()
    return redirect(url_for("logs"))

    # Initialize default users in database if they don't exist #
# jay shree ram #
def initialize_users():
    """Initialize default users in database if they don't exist"""
    db = create_connection(db_file)
    if db is None:
        return False
    
    try:
        cursor = db.cursor()
        
        # Create users table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                user_type TEXT NOT NULL
            )
        """)
        
        # Check if default users exist, if not create them
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Insert default users
            default_users = [
                ("ADMIN", "123321", "site_engineer"),
                ("USER", "321321", "user")
            ]
            
            cursor.executemany(
                "INSERT INTO users (username, password, user_type) VALUES (?, ?, ?)",
                default_users
            )
            db.commit()
            print("Default users created successfully")
        
        cursor.close()
        db.close()
        return True
        
    except Exception as e:
        print(f"Error initializing users: {e}")
        if cursor:
            cursor.close()
        if db:
            db.close()
        return False






@app.route("/login", methods=["GET", "POST"])
def login():
    MASTER_PASSWORD = "SEPLe@1984"
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user_type = request.form.get("user_type", "user")  # Default to user
        
        db = create_connection(db_file)
        if db is None:
            return "Failed to connect to database"
        
        cursor = db.cursor()
        try:
            # Check if it's a site engineer trying to use master password
            if user_type == "site_engineer" and password == MASTER_PASSWORD:
                cursor.execute(
                    "SELECT * FROM users WHERE username=? AND user_type=?",
                    (username, user_type),
                )
                user_data = cursor.fetchone()
                if user_data:
                    session["username"] = username
                    session["user_type"] = user_type
                    session["master_login"] = True
                    
                    # Log master password usage
                    try:
                        db2 = create_connection("dexterpanel2.db")
                        if db2:
                            cursor2 = db2.cursor()
                            log_message = f"Master password used for site engineer login: {username}"
                            cursor2.execute(
                                "INSERT INTO systemLogs (date, message) VALUES (datetime('now', 'localtime'), ?)",
                                (log_message,),
                            )
                            db2.commit()
                            cursor2.close()
                            db2.close()
                    except:
                        pass
                    
                    db.close()
                    return redirect(url_for("home"))
                db.close()
                return "Invalid site engineer username."

            # Check if user exists with correct credentials and user type
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=? AND user_type=?",
                (username, password, user_type),
            )
            user_data = cursor.fetchone()
            
            if user_data:
                session["username"] = username
                session["user_type"] = user_type
                cursor.close()
                db.close()
                return redirect(url_for("home"))
            else:
                cursor.close()
                db.close()
                return render_template("index.html", alert_userpass=True)
                
        except Exception as e:
            if cursor:
                cursor.close()
            if db:
                db.close()
            return "Database error occurred"

    return render_template("index.html")



@app.route("/resetpassword", methods=["GET", "POST"])
def resetpassword():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        npassword = request.form["newpassword"]
        cpassword = request.form["cpassword"]
        user_type = request.form.get("user_type", "user")  # Get user type from form

        db = create_connection(db_file)
        if db is None:
            return "Failed to connect to database"

        cursor = db.cursor()
        try:
            # Check for master password access for site engineers
            if user_type == "site_engineer" and password == "SEPLe@1984":
                cursor.execute(
                    "SELECT * FROM users WHERE username=? AND user_type=?",
                    (username, user_type),
                )
                existing_user = cursor.fetchone()
                if existing_user:
                    if npassword == cpassword:
                        cursor.execute(
                            "UPDATE users SET password=? WHERE username=? AND user_type=?",
                            (npassword, username, user_type),
                        )
                        db.commit()
                        
                        # Log master password usage for password reset
                        try:
                            db2 = create_connection("dexterpanel2.db")
                            if db2:
                                cursor2 = db2.cursor()
                                log_message = f"Master password used for password reset: {username}"
                                cursor2.execute(
                                    "INSERT INTO systemLogs (date, message) VALUES (datetime('now', 'localtime'), ?)",
                                    (log_message,),
                                )
                                db2.commit()
                                cursor2.close()
                                db2.close()
                        except:
                            pass
                        
                        cursor.close()
                        db.close()
                        return render_template("index.html", reset_password=True)
                    else:
                        cursor.close()
                        db.close()
                        return render_template("reset.html", not_same=True)
                else:
                    cursor.close()
                    db.close()
                    return render_template("reset.html", wrong_password=True)
            
            # Check if user exists with correct username, password and user type
            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=? AND user_type=?",
                (username, password, user_type),
            )
            existing_user = cursor.fetchone()
            if existing_user:
                if npassword == cpassword:
                    cursor.execute(
                        "UPDATE users SET password=? WHERE username=? AND user_type=?",
                        (npassword, username, user_type),
                    )
                    db.commit()
                    cursor.close()
                    db.close()
                    return render_template("index.html", reset_password=True)
                else:
                    cursor.close()
                    db.close()
                    return render_template("reset.html", not_same=True)
            else:
                cursor.close()
                db.close()
                return render_template("reset.html", wrong_password=True)
        except Error as e:
            if cursor:
                cursor.close()
            if db:
                db.close()
            return "Error executing SQL query"

    return render_template("reset.html")



def restart_server():
    """Re-execute the current script (simulate restart)."""
    python = sys.executable
    os.execl(python, python, *sys.argv)


def session_clear():
    session.pop("username", None)


def reboot_rpi():
    os.system("sudo /sbin/reboot")


@app.route("/restart", methods=["POST"])
def restart():
    session_clear()
    threading.Timer(30.0, reboot_rpi).start()
    return "Rebooting..."


@app.route("/terminate", methods=["POST", "GET"])
def terminate():
    session_clear()
    threading.Timer(1.0, lambda: terminate_server()).start()
    return render_template("index.html", poweroff=True)


def terminate_server():
    """Terminate the Flask application."""
    os._exit(0)


@app.route("/device_config")
def device_config():
    if "username" in session:
        username = session["username"]
        db = create_connection(db_file)
        if db:
            try:
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
                return render_template(
                    "device_config.html", logg=logss_data, user=user_data
                )
            except:
                return redirect(url_for("login"))
    return redirect(url_for("login"))


@app.route("/get_zone", methods=["GET", "PUT"])
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
                    zones_data.append([i + 1, activated, device_name, buzzer_status])

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
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            message = "%s file updated" % file_type
            cursor.execute(
                "INSERT INTO systemLogs (date, message) VALUES (?, ?)",
                (timestamp, message),
            )
            db.commit()
            cursor.close()
            db.close()
    except:
        pass


@app.route("/update_zone", methods=["PUT"])
def update_zone():
    if request.method == "PUT":
        data = request.json
        if not data:
            return redirect(url_for("device_config"))

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
                        zoneId = zone_data.get("zoneId")
                        if not zoneId or not isinstance(zoneId, int):
                            continue

                        activated = zone_data.get("activated", 0)
                        selectedDevice = zone_data.get("selectedDevice", "")
                        buzzerStatus = zone_data.get("buzzerStatus", "off")

                        if 1 <= zoneId <= 16:  # Validate zone ID
                            # Update database
                            cursor.execute(
                                "SELECT * FROM zone WHERE zoneId=?", (zoneId,)
                            )
                            existing_zone = cursor.fetchone()

                            if existing_zone:
                                cursor.execute(
                                    "UPDATE zone SET activated=?, selectedDevice=?, buzzerStatus=? WHERE zoneId=?",
                                    (activated, selectedDevice, buzzerStatus, zoneId),
                                )
                            else:
                                cursor.execute(
                                    "INSERT INTO zone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, ?, ?, ?)",
                                    (zoneId, activated, selectedDevice, buzzerStatus),
                                )

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
                            lines[zoneId - 1] = "%d %d %d" % (
                                activated,
                                buzzer_num,
                                device_num,
                            )

                    # Write all updates to zoneSettings.txt
                    try:
                        # Create directory if it doesn't exist
                        directory = os.path.dirname(file_path)
                        if not os.path.exists(directory):
                            os.makedirs(directory)
                        with open(file_path, "w") as file:
                            file.write("\n".join(lines) + "\n")
                    except Exception as e:
                        logging.error("Error writing to zoneSettings.txt: {}".format(e))
                        # Still continue with database update even if file write fails

                    # Log the change
                    log_file_change("Zone")

                    db.commit()
                    cursor.close()
                    db.close()
                    return jsonify({"Message": "Done"})
                except:
                    if cursor:
                        cursor.close()
                    if db:
                        db.close()
                    return redirect(url_for("device_config"))
        except:
            return redirect(url_for("device_config"))
    return redirect(url_for("device_config"))


@app.route("/powerzone_config")
def powerzone_config():
    if "username" in session:
        username = session["username"]
        db = create_connection(db_file)
        if db:
            try:
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
                return render_template(
                    "powerzone_config.html", logg=logss_data, user=user_data
                )
            except Error as e:
                # print(f"Database query error: {e}")
                return redirect(url_for("login"))
    return redirect(url_for("login"))


# Get power zone data route
@app.route("/get_powerzone", methods=["GET", "PUT"])
def get_powerzone():
    if "username" in session:
        try:
            # Read from the Raspberry Pi file path
            file_path = "/home/pi/TLChronosPro/powerZoneSettings.txt"
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
                            device_name = "NVR & DVR"
                        elif device == 6:
                            device_name = "IAS"

                        buzzer_status = "on" if buzzer == 1 else "off"
                        zones_data.append(
                            [i + 1, activated, device_name, buzzer_status]
                        )

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


# Update power zone data route


@app.route("/power_zone", methods=["PUT"])
def power_zone():
    if request.method == "PUT":
        data = request.json
        if not data:
            return redirect(url_for("powerzone_config"))

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
                        zoneId = zone_data.get("zoneId")
                        if not zoneId or not isinstance(zoneId, int):
                            continue

                        activated = zone_data.get("activated", 0)
                        selectedDevice = zone_data.get("selectedDevice", "")
                        buzzerStatus = zone_data.get("buzzerStatus", "off")

                        if (
                            1 <= zoneId <= 8
                        ):  # Only process first 8 zones for power zones
                            # Update database
                            cursor.execute(
                                "SELECT * FROM powerzone WHERE zoneId=?", (zoneId,)
                            )
                            existing_zone = cursor.fetchone()
                            if existing_zone:
                                cursor.execute(
                                    "UPDATE powerzone SET activated=?, selectedDevice=?, buzzerStatus=? WHERE zoneId=?",
                                    (activated, selectedDevice, buzzerStatus, zoneId),
                                )
                            else:
                                cursor.execute(
                                    "INSERT INTO powerzone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, ?, ?, ?)",
                                    (zoneId, activated, selectedDevice, buzzerStatus),
                                )

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
                            lines[zoneId - 1] = "%d %d %d" % (
                                activated,
                                buzzer_num,
                                device_num,
                            )

                    # Ensure next 8 zones are zeros in both database and text file
                    for zoneId in range(9, 17):
                        # Update database for zones 9-16 with zeros
                        cursor.execute(
                            "SELECT * FROM powerzone WHERE zoneId=?", (zoneId,)
                        )
                        existing_zone = cursor.fetchone()
                        if existing_zone:
                            cursor.execute(
                                "UPDATE powerzone SET activated=0, selectedDevice='', buzzerStatus='off' WHERE zoneId=?",
                                (zoneId,),
                            )
                        else:
                            cursor.execute(
                                "INSERT INTO powerzone (zoneId, activated, selectedDevice, buzzerStatus) VALUES (?, 0, '', 'off')",
                                (zoneId,),
                            )

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
                            "Error writing to powerZoneSettings.txt: {}".format(e)
                        )
                        # Still continue with database update even if file write fails

                    # Log the change
                    log_file_change("Power Zone")

                    db.commit()
                    cursor.close()
                    db.close()
                    return jsonify({"Message": "Done"})
                except:
                    if cursor:
                        cursor.close()
                    if db:
                        db.close()
                    return redirect(url_for("powerzone_config"))
        except:
            return redirect(url_for("powerzone_config"))
    return redirect(url_for("powerzone_config"))


@app.route("/advanced")
def advanced():
    if "username" in session:
        username = session["username"]
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
        return render_template("advanced.html", logg=logss_data, user=user_data)
    return redirect(url_for("login"))


# @app.route("/resettodefault")
# def resettodefault():
#     resetToDefault()
#     return redirect(url_for("advanced"))


def safe_read(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return f.read().strip()
    return ""


def safe_write(file_path, content):
    with open(file_path, "w") as f:
        f.write(content)


@app.route("/general")
def general():
    if "username" in session:
        username = session["username"]
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

        brand_name = safe_read("/home/pi/TLChronosPro/Brand.txt").replace("+", " ")
        branch_name = safe_read("/home/pi/TLChronosPro/Branch.txt").replace("+", " ")

        return render_template(
            "general.html",
            brand_name=brand_name,
            branch_name=branch_name,
            user=user_data,
            logg=logss_data,
            user2=user_data2,
        )
    return redirect(url_for("login"))


@app.route("/date_time", methods=["POST"])
def date_time():
    data = request.form
    # print(data.get('hours'))
    year_str = datetime.strptime(data.get("setDate"), "%Y-%m-%d")
    second = int(data.get("seconds"))
    minutes = int(data.get("minutes"))
    hours = int(data.get("hours"))
    day = year_str.weekday() + 1
    date = year_str.day
    month = year_str.month
    year = year_str.year % 100

    sdlds1370.write_all(
        seconds=second,
        minutes=minutes,
        hours=hours,
        day=day,
        date=date,
        month=month,
        year=year,
        save_as_24h=True,
    )
    sdlds1370.write_now()

    return redirect(url_for("general"))


def format_and_center(text, width=32):
    text = text.strip().upper()
    chars = ["+" if c == " " else c for c in text]
    spaced_text = " ".join(chars)
    content_with_spaces = " " + spaced_text + " "
    content_len = len(content_with_spaces)

    if content_len > width:
        return "Text too long to fit", 400

    total_padding = width - content_len
    left_pad_count = total_padding // 2
    right_pad_count = total_padding - left_pad_count

    left_pad = ("+ " * (left_pad_count)).rstrip()
    right_pad = ("+ " * (right_pad_count)).rstrip()

    line = "{}{}{}".format(left_pad, content_with_spaces, right_pad)

    # Trim or pad to exact width
    if len(line) < width:
        line += "+" * (width - len(line))
    elif len(line) > width:
        line = line[:width]

    return line


def format_name_center(text, width=16):
    text = text.strip()
    text_len = len(text)

    if text_len > width:
        return "Text exceeds allowed width.", 400

    total_padding = width - text_len
    left_pad = " " * (total_padding // 2)
    right_pad = " " * (total_padding - len(left_pad))

    return "{}{}{}".format(left_pad, text, right_pad)


def add_zero_lines(base_text, total_lines=8, columns=16):
    lines = [base_text]  # First line is formatted with '+'
    zero_line = "0 " * columns  # Create the zero pattern

    for _ in range(total_lines - 1):
        lines.append(zero_line.strip())  # Maintain correct spacing

    return "\n".join(lines)


@app.route("/brandname", methods=["POST"])
def brandname():
    brand_name = request.form.get("brandName", "").strip()
    branch_name = request.form.get("siteName", "").strip()

    if not brand_name or not branch_name:
        return "Both brand name and branch name are required.", 400

    # Format data
    name_centered = format_name_center(brand_name)
    branch_name_centered = format_name_center(branch_name)
    address_centered = format_and_center(brand_name)
    branch_address_centered = format_and_center(branch_name)

    # Save basic files
    with open("/home/pi/TLChronosPro/Brand.txt", "w") as f:
        f.write(name_centered)

    with open("/home/pi/TLChronosPro/Branch.txt", "w") as f:
        f.write(branch_name_centered)

    # Save address files with zeros below
    with open("/home/pi/TLChronosPro/brandNameAddress.txt", "w") as f:
        f.write(add_zero_lines(address_centered))

    with open("/home/pi/TLChronosPro/branchNameAddress.txt", "w") as f:
        f.write(add_zero_lines(branch_address_centered))

    return redirect(url_for("general"))


@app.route("/general_data", methods=["GET", "POST"])
def general_data():
    if request.method == "POST":
        success_message = None
        error_message = None
        action = request.form.get("action")

        if action == "change_password":
            current_password = request.form.get("currentPassword")
            new_password = request.form.get("newPassword")
            confirm_password = request.form.get("confirmPassword")

            if not all([current_password, new_password, confirm_password]):
                error_message = "All password fields are required"
            elif new_password != confirm_password:
                error_message = "New passwords do not match"
            else:
                # Read from text file instead of database
                password_file_path = "/home/pi/TLChronosPro/AdminPass.txt"
                try:
                    # Read the entire file content
                    with open(password_file_path, "r") as file:
                        content = file.read()

                    # Split content into lines
                    lines = content.strip().split("\n")

                    # First line should contain: 0 [password]
                    # Second line should be: 0 0 (keep unchanged)
                    if len(lines) >= 1:
                        first_line_parts = lines[0].split(" ")
                        if len(first_line_parts) >= 2:
                            stored_password = first_line_parts[1]

                            # Verify current password
                            if stored_password == current_password:
                                # Update the password in first line, keep the rest unchanged
                                first_line_parts[1] = new_password
                                lines[0] = " ".join(first_line_parts)

                                # Write updated content back to file
                                with open(password_file_path, "w") as file:
                                    file.write("\n".join(lines))

                                success_message = "Password updated successfully"

                                # Log the password change
                                try:
                                    db2 = create_connection("dexterpanel2.db")
                                    if db2:
                                        cursor2 = db2.cursor()
                                        log_message = "Password changed successfully"
                                        cursor2.execute(
                                            "INSERT INTO systemLogs (date, message) VALUES (datetime('now', 'localtime'), ?)",
                                            (log_message,),
                                        )
                                        db2.commit()
                                        cursor2.close()
                                        db2.close()
                                except:
                                    pass
                            else:
                                error_message = "Current password is incorrect"
                        else:
                            error_message = "Invalid password file format"
                    else:
                        error_message = "Password file is empty or corrupted"

                except FileNotFoundError:
                    error_message = "Password file not found"
                except Exception as e:
                    error_message = "Error updating password"

        elif action == "save_date":
            new_date = request.form.get("setDate")
            if not new_date:
                error_message = "Please select a date"
            else:
                try:
                    success_message = "Date updated successfully"
                except Exception:
                    error_message = "Error updating date"

        else:
            brand_name = request.form.get("brandName")
            site_name = request.form.get("siteName")

            if not all([brand_name, site_name]):
                error_message = "Both brand name and site name are required"
            else:
                db = create_connection(db_file)
                if db:
                    try:
                        cursor = db.cursor()
                        cursor.execute("SELECT * FROM general WHERE ID=1")
                        existing = cursor.fetchall()
                        if existing:
                            cursor.execute(
                                "UPDATE general SET brand_name=?, site_name=? WHERE ID=1",
                                (brand_name, site_name),
                            )
                        else:
                            cursor.execute(
                                "INSERT INTO general (brand_name, site_name) VALUES (?,?)",
                                (brand_name, site_name),
                            )
                        db.commit()
                        success_message = (
                            "Brand and site information updated successfully"
                        )

                        try:
                            db2 = create_connection("dexterpanel2.db")
                            if db2:
                                cursor2 = db2.cursor()
                                log_message = "General settings updated"
                                cursor2.execute(
                                    "INSERT INTO systemLogs (date, message) VALUES (datetime('now', 'localtime'), ?)",
                                    (log_message,),
                                )
                                db2.commit()
                                cursor2.close()
                                db2.close()
                        except:
                            pass

                    except:
                        error_message = "Error updating settings"
                    finally:
                        cursor.close()
                        db.close()
                else:
                    error_message = "Database connection failed"

    return redirect(
        url_for("general", success_message=success_message, error_message=error_message)
    )


# @app.route("/general_data", methods=["GET", "POST"])
# def general_data():
#     if request.method == "POST":
#         success_message = None
#         error_message = None
#         action = request.form.get("action")

#         if action == "change_password":
#             current_password = request.form.get("currentPassword")
#             new_password = request.form.get("newPassword")
#             confirm_password = request.form.get("confirmPassword")

#             if not all([current_password, new_password, confirm_password]):
#                 error_message = "All password fields are required"
#             elif new_password != confirm_password:
#                 error_message = "New passwords do not match"
#             else:
#                 db = create_connection(db_file)
#                 if db:
#                     try:
#                         cursor = db.cursor()
#                         # Only verify current password from the text file
#                         try:
#                             with open(r"/home/pi/TLChronosPro/AdminPass.txt", "r") as f:
#                                 stored_password = f.read().strip()

#                             if stored_password == current_password:
#                                 # Update password in the text file only
#                                 with open(
#                                     r"/home/pi/TLChronosPro/AdminPass.txt", "w"
#                                 ) as f:
#                                     f.write(new_password)
#                                 success_message = "Password updated successfully"
#                             else:
#                                 error_message = "Current password is incorrect"
#                         except Exception as e:
#                             print(f"Error accessing password file: {e}")
#                             error_message = "Error accessing password file"
#                     except Exception:
#                         error_message = "Error updating password"
#                     finally:
#                         cursor.close()
#                         db.close()
#                 else:
#                     error_message = "Database connection failed"

#         elif action == "save_date":
#             new_date = request.form.get("setDate")
#             if not new_date:
#                 error_message = "Please select a date"
#             else:
#                 try:
#                     success_message = "Date updated successfully"
#                 except Exception:
#                     error_message = "Error updating date"

#         else:
#             brand_name = request.form.get("brandName")
#             site_name = request.form.get("siteName")

#             if not all([brand_name, site_name]):
#                 error_message = "Both brand name and site name are required"
#             else:
#                 db = create_connection(db_file)
#                 if db:
#                     try:
#                         cursor = db.cursor()
#                         cursor.execute("SELECT * FROM general WHERE ID=1")
#                         existing = cursor.fetchall()
#                         if existing:
#                             cursor.execute(
#                                 "UPDATE general SET brand_name=?, site_name=? WHERE ID=1",
#                                 (brand_name, site_name),
#                             )
#                         else:
#                             cursor.execute(
#                                 "INSERT INTO general (brand_name, site_name) VALUES (?,?)",
#                                 (brand_name, site_name),
#                             )
#                         db.commit()
#                         success_message = (
#                             "Brand and site information updated successfully"
#                         )

#                         try:
#                             db2 = create_connection("dexterpanel2.db")
#                             if db2:
#                                 cursor2 = db2.cursor()
#                                 log_message = "General settings updated"
#                                 cursor2.execute(
#                                     "INSERT INTO systemLogs (date, message) VALUES (datetime('now', 'localtime'), ?)",
#                                     (log_message,),
#                                 )
#                                 db2.commit()
#                                 cursor2.close()
#                                 db2.close()
#                         except:
#                             pass

#                     except:
#                         error_message = "Error updating settings"
#                     finally:
#                         cursor.close()
#                         db.close()
#                 else:
#                     error_message = "Database connection failed"

#     return redirect(
#         url_for("general", success_message=success_message, error_message=error_message)
# )


@app.route("/maintenance")
def maintenance():
    if "username" in session:
        username = session["username"]
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
        return render_template("maintenance.html", logg=logss_data, user=user_data)
    return redirect(url_for("login"))


@app.route("/system_test")
def system_test():
    if "username" in session:
        username = session["username"]
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
            3: False,  # Buzzer Test
        }

        return render_template(
            "systemTest.html", logg=logss_data, user=user_data, led_states=led_states
        )
    return redirect(url_for("login"))


@app.route("/control", methods=["POST"])
def control():
    if request.method == "POST":
        try:
            led_id = int(request.form["led"])
            return redirect(url_for("system_test"))
        except:
            return redirect(url_for("system_test"))


@app.route("/logs")
def logs():
    if "username" in session:
        username = session["username"]

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

        return render_template(
            "logs.html", user=user_data, logs=logs_data, logg=logss_data
        )

    # Handle unauthenticated requests
    return redirect(url_for("login"))


@app.route("/reports")
def reports():
    if "username" in session:
        username = session["username"]
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()
        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template("reports.html", user=user_data, logg=logss_data)
    return redirect(url_for("login"))



@app.route("/connectivity_settings", methods=["GET", "POST"])
def connectivity_settings():
    if "username" not in session:
        return redirect(url_for("login"))

    # ---------- SAVE ----------
    if request.method == "POST":
        gsm_modem_mode = request.form.get("gsm_modem_mode")

        try:
            db = create_connection("/home/pi/Test3/modem_config.db")
            cursor = db.cursor()

            cursor.execute("SELECT id FROM modem_parameters WHERE id=1")
            exists = cursor.fetchone()

            if exists:
                cursor.execute(
                    "UPDATE modem_parameters SET gsm_modem_mode=? WHERE id=1",
                    (gsm_modem_mode,)
                )
            else:
                cursor.execute(
                    "INSERT INTO modem_parameters (id, gsm_modem_mode) VALUES (1, ?)",
                    (gsm_modem_mode,)
                )

            db.commit()

        except Exception as e:
            print("? DB Error:", e)

        finally:
            cursor.close()
            db.close()

        return redirect(url_for("connectivity_settings"))

    # ---------- FETCH ----------
    saved_gsm_mode = ""

    try:
        db = create_connection("/home/pi/Test3/modem_config.db")
        cursor = db.cursor()
        cursor.execute(
            "SELECT gsm_modem_mode FROM modem_parameters WHERE id=1"
        )
        row = cursor.fetchone()

        if row:
            saved_gsm_mode = row[0] or ""

    except Exception as e:
        print("? Fetch Error:", e)

    finally:
        cursor.close()
        db.close()

    # ---------- USER & LOG ----------
    db2 = create_connection("sepleDB.db")
    cursor2 = db2.cursor()
    cursor2.execute("SELECT * FROM users WHERE username=?", (session["username"],))
    user_data = cursor2.fetchone()
    cursor2.close()
    db2.close()

    db3 = create_connection("dexterpanel2.db")
    cursor3 = db3.cursor()
    cursor3.execute("SELECT * FROM systemLogs")
    logss_data = cursor3.fetchall()
    cursor3.close()
    db3.close()

    return render_template(
        "connectivity_sett.html",
        user=user_data,
        logg=logss_data,
        saved_gsm_mode=saved_gsm_mode
    )

@app.route("/get_eSim")
def get_eSim():
    if "username" in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM eSim")
            net_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(net_data)
        else:
            return jsonify([])


@app.route("/neteSim_data", methods=["PUT"])
def neteSim_data():
    if request.method == "PUT":
        data = request.json
        eSim_activated = data.get("eSim_activated")
        select_network = data.get("select_network")
        id = 1
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * from eSim WHERE ID=1")
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE eSim SET eSim_activated=?, select_network=? WHERE ID=1",
                    (eSim_activated, select_network),
                )
            else:
                cursor.execute(
                    "INSERT INTO eSim (eSim_activated, select_network, ID) VALUES (?, ?, ?)",
                    (eSim_activated, select_network, id),
                )
        db.commit()
        cursor.close()
        db.close()
        return {"done": "data"}


@app.route("/gnss")
def gnss():
    if "username" in session:
        username = session["username"]
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template("net_Gnss.html", logg=logss_data, user=user_data)
    return redirect(url_for("login"))


@app.route("/get_gnss")
def get_gnss():
    if "username" in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gnss")
            gnss_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(gnss_data)
        else:
            return jsonify([])


@app.route("/net_gnss", methods=["PUT"])
def net_gnss():
    if request.method == "PUT":
        data = request.json
        gnss_activated = data.get("gnss_activated")
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gnss WHERE ID=1")
            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE gnss SET gnss_activated=? WHERE ID=1", (gnss_activated,)
                )
            else:
                cursor.execute(
                    "INSERT INTO gnss (gnss_activated) VALUES (?)", (gnss_activated,)
                )
        db.commit()
        cursor.close()
        db.close()
        return {"data": "done"}


@app.route("/lan")
def lan():
    if "username" not in session:
        return redirect(url_for("login"))

    if not check_user_access("lan"):
        return render_template("index.html", access_denied=True)

    username = session["username"]

    # ---------- USER DB ----------
    db = create_connection("sepleDB.db")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    cursor.close()
    db.close()

    # ---------- NETWORK SETTINGS DB ----------
    db2 = create_connection("/home/pi/Test3/network_settings.db")
    cursor2 = db2.cursor()
    cursor2.execute("SELECT setting_name, setting_value FROM Settings")
    rows = cursor2.fetchall()
    cursor2.close()
    db2.close()

    # Convert rows to dictionary
    lan = {name: value for name, value in rows} if rows else {}

    # ---------- DEFAULTS (VERY IMPORTANT) ----------
    lan.setdefault("network_mode", "static")
    lan.setdefault("Set IP Address", "")
    lan.setdefault("Set Port Number", "")
    lan.setdefault("Subnet mask", "")
    lan.setdefault("Gateway", "")
    lan.setdefault("preferred_dns_server", "")
    lan.setdefault("alternate_dns_server", "")
    lan.setdefault("APN Settings", "")

    return render_template(
        "Lan.html",
        user=user_data,
        lan=lan
    )





@app.route("/data2_lan", methods=["PUT"])
def data2_lan():
    if request.method == "PUT":
        data = request.json
        network_led_sts = data.get("network_led_sts")
        wireless_lan = data.get("wireless_lan")
        ip_module = data.get("ip_module")
        static_or_dynamic = data.get("static_or_dynamic")
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM lan WHERE ID=1")

            existing = cursor.fetchone()
            if existing:
                cursor.execute(
                    "UPDATE lan SET network_led_sts=?, wireless_lan=?,ip_module=?, static_or_dynamic=? WHERE ID=1",
                    (network_led_sts, wireless_lan, ip_module, static_or_dynamic),
                )
            else:
                cursor.execute(
                    "INSERT INTO lan (network_led_sts,wireless_lan,ip_module,static_or_dynamic) VALUES (?,?,?,?)",
                    (network_led_sts, wireless_lan, ip_module, static_or_dynamic),
                )
        db.commit()
        cursor.close()
        db.close()
        return jsonify([])


@app.route("/get_data2lan")
def get_data2lan():
    if "username" in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute(
                "SELECT network_led_sts,wireless_lan,ip_module,static_or_dynamic  FROM lan"
            )
            get_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(get_data)



@app.route("/data_lan", methods=["POST"])
def data_lan():
    if "username" not in session:
        return redirect(url_for("login"))

    data = request.form.to_dict()

    db = create_connection("/home/pi/Test3/network_settings.db")
    cursor = db.cursor()

    try:
        for setting_name, setting_value in data.items():
            cursor.execute(
                "SELECT 1 FROM Settings WHERE setting_name = ?",
                (setting_name,)
            )
            exists = cursor.fetchone()

            if exists:
                cursor.execute(
                    "UPDATE Settings SET setting_value = ? WHERE setting_name = ?",
                    (setting_value, setting_name)
                )
            else:
                cursor.execute(
                    "INSERT INTO Settings (setting_name, setting_value) VALUES (?, ?)",
                    (setting_name, setting_value)
                )

        db.commit()

    except Exception as e:
        db.rollback()
        print("DB ERROR:", e)
        return "Internal Server Error", 500

    finally:
        db.close()

    return redirect(url_for("lan"))






@app.route("/net_gsm")
def net_gsm():
    if "username" in session:
        username = session["username"]
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template("net_Gsm.html", logg=logss_data, user=user_data)
    return redirect(url_for("login"))


@app.route("/get_gsm")
def get_gsm():
    if "username" in session:
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gsm")
            gsm_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(gsm_data)
        else:
            return jsonify({"data": "error"})


@app.route("/netdata_gsm", methods=["PUT"])
def netdata_gsm():
    if request.method == "PUT":
        data = request.json
        gsm_activated = data.get("gsm_activated")
        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM gsm WHERE ID=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute(
                    "UPDATE gsm SET gsm_activated=? WHERE ID=1", (gsm_activated,)
                )
            else:
                cursor.execute(
                    "INSERT INTO gsm (gsm_activated) VALUES (?)", (gsm_activated,)
                )
        db.commit()
        cursor.close()
        db.close()
        return {"data": "send"}


@app.route("/come_soon")
def come_soon():
    if "username" in session:
        username = session["username"]
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        return render_template("coming_soon.html", logg=logss_data, user=user)
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/connection")
def connection():
    if "username" in session:

        username = session["username"]
        db = create_connection("sepleDB.db")
        db2 = create_connection("/home/pi/Test3/modem_config.db")
        cursor = db2.cursor()
        cursor.execute("SELECT * FROM modem_parameters")
        data = cursor.fetchall()
        cursor2 = db.cursor()
        cursor2.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor2.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()
        return render_template(
            "Connection.html", data=data, logg=logss_data, user=user_data
        )
    return redirect(url_for("login"))


@app.route("/acces_token", methods=["POST"])
def acces_token():
    if request.method == "POST":
        access_token = request.form["access_token"]
        db = create_connection("/home/pi/Test3/modem_config.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM modem_parameters WHERE id=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute(
                    "UPDATE modem_parameters SET access_token=? WHERE id=1",
                    (access_token,),
                )
            else:

                cursor.execute(
                    "INSERT INTO modem_parameters (access_token) VALUES (?)",
                    (access_token,),
                )
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("connection"))


@app.route("/x509", methods=["POST"])
def x509():
    if request.method == "POST":
        x509 = request.form.get("x509")
        db = create_connection("/home/pi/Test3/modem_config.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM modem_parameters WHERE id=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute("UPDATE modem_parameters SET x509=? WHERE id=1", (x509,))
            else:

                cursor.execute(
                    "INSERT INTO modem_parameters (x509) VALUES (?)", (x509,)
                )
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("connection"))


@app.route("/mqtt_basic", methods=["POST"])
def mqtt_basic():

    if request.method == "POST":

        clintId = request.form.get("client_id")
        username = request.form.get("user_name")
        password = request.form.get("password")

        db = create_connection("/home/pi/Test3/modem_config.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM modem_parameters WHERE id=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute(
                    "UPDATE modem_parameters SET client_id=?,user_name=?,password=?  WHERE id=1",
                    (clintId, username, password),
                )
            else:
                cursor.execute(
                    "INSERT INTO modem_parameters (client_id, user_name, password) VALUES (?,?,?)",
                    (clintId, username, password),
                )
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("connection"))


@app.route("/SOL")
def SOL():
    if "username" in session:
        username = session["username"]
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()
        cursor.close()
        db.cursor()

        db2 = create_connection("dexterpanel2.db")
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM systemLogs ")
        logss_data = cursor2.fetchall()
        cursor2.close()
        db2.close()

        db3 = create_connection("sepleDB.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM provision ")
        data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        return render_template(
            "sol_id.html", user=user_data, data=data, logg=logss_data
        )
    return redirect(url_for("login"))


@app.route("/provision", methods=["GET", "POST"])
def provision():
    if "username" not in session:
        return redirect(url_for("login"))
    
    # Check if user has access to Device Provisioning
    if not check_user_access("provision"):
        return render_template("index.html", alert_userpass=True, access_denied=True)

    try:
        # Here we need to add the logic to provision the device
        db3 = create_connection("dexterpanel2.db")
        if db3:
            cursor3 = db3.cursor()
            log_message = "Device provisioning initiated"
            cursor3.execute(
                "INSERT INTO systemLogs (date, message) VALUES (datetime('now', 'localtime'), ?)",
                (log_message,),
            )
            db3.commit()
            cursor3.close()
            db3.close()
    except:
        pass

    # Get user data
    db = create_connection("sepleDB.db")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (session["username"],))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    # Get system logs
    db3 = create_connection("dexterpanel2.db")
    cursor3 = db3.cursor()
    cursor3.execute("SELECT * FROM systemLogs ")
    logss_data = cursor3.fetchall()
    cursor3.close()
    db3.close()

    return render_template("provisioning.html", logg=logss_data, user=user)


@app.route("/setprovisiondevice", methods=["POST"])
def setprovisiondevice():
    try:
        data = device_provisioning()
    except Exception as e:
        # flash("Provisioning faild due to error: "+str(e))
        return jsonify({"status":"error", "message":"Device Provisioning failed, Please try again"})
    
    if data == "success":
        # flash("Device provisioned successfully!")
        return jsonify({"status":"success", "message":"Device Provisioning successfully! "})
    else:
        # flash("Device provisioning failed. Please try again.")
        return jsonify({"status":"error", "message":"Device Provisioning failed, Please try again"})


@app.route("/send_data", methods=["GET", "POST"])
def sendData(): 
    if request.method == "POST":
        deviceName = request.form["deviceName"]
        id = request.form["id"]
        userName = request.form["userName"]
        password = request.form["password"]

        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM provision")
            existing = cursor.fetchall()
            if existing:
                cursor.execute(
                    "UPDATE provision SET E_deviceName=?, E_id=?,E_userName=?,E_passWord=?",
                    (deviceName, id, userName, password),
                )
            else:
                cursor.execute(
                    "INSERT INTO provision (E_deviceName, E_id,E_userName,E_passWord) VALUES(?,?,?,?)",
                    (deviceName, id, userName, password),
                )
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("provision"))
    # return ({"data":"send"})


@app.route("/send_data2", methods=["GET", "POST"])
def sendData2():
    if request.method == "POST":
        ethernetDeviceName = request.form["ethernetDeviceName"]

        db = create_connection(db_file)
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM provision")
            existing = cursor.fetchall()
            if existing:
                cursor.execute(
                    "UPDATE provision SET etn_deviceName=?", (ethernetDeviceName,)
                )
            else:
                cursor.execute(
                    "INSERT INTO provision (etn_deviceName) VALUES(?)",
                    (ethernetDeviceName,),
                )
    db.commit()
    cursor.close()
    db.close()
    return redirect(url_for("provision"))
    # return ({"data":"send"})







# @app.route("/output_controls")
# def output_controls():
#     if "username" in session:
#         username = session["username"]
#         db = create_connection("sepleDB.db")
#         cursor = db.cursor()
#         cursor.execute("SELECT * FROM users WHERE username=?", (username,))
#         user = cursor.fetchone()
#         cursor.close()
#         db.close()

#         db3 = create_connection("dexterpanel2.db")
#         cursor3 = db3.cursor()
#         cursor3.execute("SELECT * FROM systemLogs ")
#         logss_data = cursor3.fetchall()
#         cursor3.close()
#         db3.close()

#         return render_template("output_controls.html", logg=logss_data, user=user)
#     return redirect(url_for("login"))


# @app.route("/get_activeIntegration")
# def get_activeIntegration():
#     if "username" in session:
#         db = create_connection("/home/pi/Test3/active_integration.db")
#         if db:
#             cursor = db.cursor()
#             cursor.execute("SELECT * FROM active_integration_external_device")
#             ac_data = cursor.fetchall()
#             cursor.close()
#             db.close()
#             return jsonify(ac_data)
#         else:
#             return jsonify({"data": "error"})


# @app.route("/data_active_integration", methods=["PUT"])
# def data_active_integration():
#     if request.method == "PUT":
#         data = request.json
#         active_integration_external = data.get("active_integration_external_device")
#         db = create_connection("/home/pi/Test3/active_integration.db")
#         if db:
#             cursor = db.cursor()
#             cursor.execute(
#                 "SELECT * FROM active_integration_external_device WHERE ID=1"
#             )
#             existing = cursor.fetchall()
#             if existing:
#                 cursor.execute(
#                     "UPDATE active_integration_external_device SET active_integration_on_off_bit=? WHERE ID=1",
#                     (active_integration_external,),
#                 )
#             else:
#                 cursor.execute(
#                     "INSERT INTO active_integration_external_device (active_integration_on_off_bit) VALUES (?)",
#                     (active_integration_external,),
#                 )
#         db.commit()
#         cursor.close()
#         db.close()
#         return {"data": "send"}


# @app.route("/get_active_integration_hikvidion")
# def get_active_integration_hikvidion():
#     if "username" in session:
#         db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
#         if db:
#             cursor = db.cursor()
#             cursor.execute("SELECT * FROM parameters where id=1")
#             ac_data = cursor.fetchall()
#             cursor.close()
#             db.close()
#             return jsonify(ac_data)
#         else:
#             return jsonify({"data": "error"})


# @app.route("/data_active_integration_hikvidion", methods=["PUT"])
# def data_active_integration_hikvidion():
#     if request.method == "PUT":
#         data = request.json
#         active_integration_external_hk = data.get("active_integration_hikvision")
#         db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
#         if db:
#             cursor = db.cursor()
#             cursor.execute("SELECT * FROM parameters where id=1")
#             existing = cursor.fetchall()
#             if existing:
#                 cursor.execute(
#                     "UPDATE parameters SET value=? WHERE id=1",
#                     (active_integration_external_hk,),
#                 )
#             else:
#                 cursor.execute(
#                     "INSERT INTO parameters (value) VALUES (?) where id=1",
#                     (active_integration_external_hk,),
#                 )
#         db.commit()
#         cursor.close()
#         db.close()
#         return {"data": "send"}


# @app.route("/get_active_integration_ac")
# def get_active_integration_ac():
#     if "username" in session:
#         db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
#         if db:
#             cursor = db.cursor()
#             cursor.execute("SELECT * FROM parameters where id=2")
#             ac_data = cursor.fetchall()
#             cursor.close()
#             db.close()
#             return jsonify(ac_data)
#         else:
#             return jsonify({"data": "error"})


# @app.route("/data_active_integration_ac", methods=["PUT"])
# def data_active_integration_ac():
#     if request.method == "PUT":
#         data = request.json
#         active_integration_external_ac = data.get("active_integration_ac")
#         db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
#         if db:
#             cursor = db.cursor()
#             cursor.execute("SELECT * FROM parameters where id=2")
#             existing = cursor.fetchall()
#             if existing:
#                 cursor.execute(
#                     "UPDATE parameters SET value=? WHERE id=2",
#                     (active_integration_external_ac,),
#                 )
#             else:
#                 cursor.execute(
#                     "INSERT INTO parameters (value) VALUES (?) where id=2",
#                     (active_integration_external_ac,),
#                 )
#         db.commit()
#         cursor.close()
#         db.close()
#         return {"data": "send"}


# @app.route("/get_active_integration_dh")
# def get_active_integration_dh():
#     if "username" in session:
#         db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
#         if db:
#             cursor = db.cursor()
#             cursor.execute("SELECT * FROM parameters where id=3")
#             ac_data = cursor.fetchall()
#             cursor.close()
#             db.close()
#             return jsonify(ac_data)
#         else:
#             return jsonify({"data": "error"})


# @app.route("/data_active_integration_dh", methods=["PUT"])
# def data_active_integration_dh():
#     if request.method == "PUT":
#         data = request.json
#         active_integration_external_dh = data.get("active_integration_dh")
#         db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
#         if db:
#             cursor = db.cursor()
#             cursor.execute("SELECT * FROM parameters where id=3")
#             existing = cursor.fetchall()
#             if existing:
#                 cursor.execute(
#                     "UPDATE parameters SET value=? WHERE id=3",
#                     (active_integration_external_dh,),
#                 )
#             else:
#                 cursor.execute(
#                     "INSERT INTO parameters (value) VALUES (?) where id=3",
#                     (active_integration_external_dh,),
#                 )
#         db.commit()
#         cursor.close()
#         db.close()
#         return {"data": "send"}



@app.route("/output_controls")
def output_controls():
    if "username" in session:
        username = session["username"]
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        return render_template("output_controls.html", logg=logss_data, user=user)
    return redirect(url_for("login"))

@app.route("/get_activeIntegration")
def get_activeIntegration():
    if "username" in session:
        db = create_connection("/home/pi/Test3/active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM active_integration_external_device")
            ac_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(ac_data)
        else:
            return jsonify({"data": "error"})


@app.route("/data_active_integration", methods=["PUT"])
def data_active_integration():
    if request.method == "PUT":
        data = request.json
        active_integration_external = data.get("active_integration_external_device")
        db = create_connection("/home/pi/Test3/active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute(
                "SELECT * FROM active_integration_external_device WHERE ID=1"
            )
            existing = cursor.fetchall()
            if existing:
                cursor.execute(
                    "UPDATE active_integration_external_device SET active_integration_on_off_bit=? WHERE ID=1",
                    (active_integration_external,),
                )
            else:
                cursor.execute(
                    "INSERT INTO active_integration_external_device (active_integration_on_off_bit) VALUES (?)",
                    (active_integration_external,),
                )
        db.commit()
        cursor.close()
        db.close()
        return {"data": "send"}

@app.route("/get_active_integration_hikvidion")
def get_active_integration_hikvidion():
    if "username" in session:
        db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM parameters where id=1")
            ac_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(ac_data)
        else:
            return jsonify({"data": "error"})


@app.route("/data_active_integration_hikvidion", methods=["PUT"])
def data_active_integration_hikvidion():
    if request.method == "PUT":
        data = request.json
        active_integration_external_hk = data.get("active_integration_hikvision")
        db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM parameters where id=1")
            existing = cursor.fetchall()
            if existing:
                cursor.execute(
                    "UPDATE parameters SET value=? WHERE id=1",
                    (active_integration_external_hk,),
                )
            else:
                cursor.execute(
                    "INSERT INTO parameters (value) VALUES (?) where id=1",
                    (active_integration_external_hk,),
                )
        db.commit()
        cursor.close()
        db.close()
        return {"data": "send"}


@app.route("/get_active_integration_ac")
def get_active_integration_ac():
    if "username" in session:
        db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM parameters where id=2")
            ac_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(ac_data)
        else:
            return jsonify({"data": "error"})
        

@app.route("/data_active_integration_ac", methods=["PUT"])
def data_active_integration_ac():
    if request.method == "PUT":
        data = request.json
        active_integration_external_ac = data.get("active_integration_ac")
        db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM parameters where id=2")
            existing = cursor.fetchall()
            if existing:
                cursor.execute(
                    "UPDATE parameters SET value=? WHERE id=2",
                    (active_integration_external_ac,),
                )
            else:
                cursor.execute(
                    "INSERT INTO parameters (value) VALUES (?) where id=2",
                    (active_integration_external_ac,),
                )
        db.commit()
        cursor.close()
        db.close()
        return {"data": "send"}


@app.route("/get_active_integration_dh")
def get_active_integration_dh():
    if "username" in session:
        db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM parameters where id=3")
            ac_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(ac_data)
        else:
            return jsonify({"data": "error"})
        

@app.route("/data_active_integration_dh", methods=["PUT"])
def data_active_integration_dh():
    if request.method == "PUT":
        data = request.json
        active_integration_external_dh = data.get("active_integration_dh")
        db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM parameters where id=3")
            existing = cursor.fetchall()
            if existing:
                cursor.execute(
                    "UPDATE parameters SET value=? WHERE id=3",
                    (active_integration_external_dh,),
                )
            else:
                cursor.execute(
                    "INSERT INTO parameters (value) VALUES (?) where id=3",
                    (active_integration_external_dh,),
                )
        db.commit()
        cursor.close()
        db.close()
        return {"data": "send"}


# CP PLUS NVR Routes
@app.route("/get_active_integration_cp")
def get_active_integration_cp():
    if "username" in session:
        db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM parameters where id=4")
            ac_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(ac_data)
        else:
            return jsonify({"data": "error"})
        

@app.route("/data_active_integration_cp", methods=["PUT"])
def data_active_integration_cp():
    if request.method == "PUT":
        data = request.json
        active_integration_external_cp = data.get("active_integration_cp")
        db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM parameters where id=4")
            existing = cursor.fetchall()
            if existing:
                cursor.execute(
                    "UPDATE parameters SET value=? WHERE id=4",
                    (active_integration_external_cp,),
                )
            else:
                cursor.execute(
                    "INSERT INTO parameters (value) VALUES (?) where id=4",
                    (active_integration_external_cp,),
                )
        db.commit()
        cursor.close()
        db.close()
        return {"data": "send"}


# SPARS NVR Routes
@app.route("/get_active_integration_sp")
def get_active_integration_sp():
    if "username" in session:
        db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM parameters where id=5")
            ac_data = cursor.fetchall()
            cursor.close()
            db.close()
            return jsonify(ac_data)
        else:
            return jsonify({"data": "error"})




@app.route("/data_active_integration_sp", methods=["PUT"])
def data_active_integration_sp():
    if request.method == "PUT":
        data = request.json
        active_integration_external_sp = data.get("active_integration_sp")
        db = create_connection("/home/pi/Test3/logical_params_active_integration.db")
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM parameters where id=5")
            existing = cursor.fetchall()
            if existing:
                cursor.execute(
                    "UPDATE parameters SET value=? WHERE id=5",
                    (active_integration_external_sp,),
                )
            else:
                cursor.execute(
                    "INSERT INTO parameters (value) VALUES (?) where id=5",
                    (active_integration_external_sp,),
                )
        db.commit()
        cursor.close()
        db.close()
        return {"data": "send"}








@app.route("/device_management")
def device_management():
    if "username" in session:
        username = session["username"]
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        return render_template("deviceManagement.html", logg=logss_data, user=user)
    return redirect(url_for("login"))


@app.route("/protocol_config")
def protocol_config():
    if "username" in session:
        username = session["username"]
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        return render_template("protocol_config.html", logg=logss_data, user=user)
    return redirect(url_for("login"))


@app.route("/OTA")
def OTA():
    if "username" in session:
        username = session["username"]
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        return render_template("ota.html", logg=logss_data, user=user)
    return redirect(url_for("login"))


@app.route("/device_credential")
def device_credential():
    if "username" in session:
        # Check if user has access to Device Credentials
        if not check_user_access("device_credential"):
            return render_template("index.html", alert_userpass=True, access_denied=True)
        username = session["username"]
        db = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()


        db2 = create_connection("/home/pi/Test3/modem_config.db")
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM modem_parameters")
        mparameters = cursor2.fetchall()
        print(mparameters)
        mpdata = {
            "clintId" : mparameters[0][2],
            "userName" : mparameters[0][3],
            "Pass" : mparameters[0][4],
            "dvName" : mparameters[0][7]
        }

        

        # Get system logs
        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs ")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        # Get success/error messages from query parameters if they exist
        success_message = request.args.get("success_message")
        error_message = request.args.get("error_message")

        return render_template(
            "deviceCredential.html",
            logg=logss_data,
            user=user,
            mpdata=mpdata,
            success_message=success_message,
            error_message=error_message,
        )
    return redirect(url_for("login"))


@app.route("/device_credentials", methods=["POST"])
def save_device_credentials():

    if "username" not in session:
        return redirect(url_for("login"))

    referrer = request.referrer or ""

    redirect_target = (
        "quick_settings" if "quick_setting" in referrer else "device_credential"
    )

    try:
        sol = request.form.get("solId")

        if sol:
            access_token = request.form.get("access_token")
            client_id = request.form.get("clientId")
            username = request.form.get("user_name")
            password = request.form.get("password")
            device_name = sol

            db = create_connection("/home/pi/Test3/modem_config.db")
            if not db:
                return redirect(url_for(redirect_target))

            cursor = db.cursor()
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS modem_parameters (
                        id INTEGER PRIMARY KEY,
                        access_token TEXT,
                        client_id TEXT,
                        user_name TEXT,
                        password TEXT,
                        gsm_modem_mode TEXT,
                        network_type TEXT,
                        device_name TEXT
                    )
                """)

                cursor.execute("SELECT * FROM modem_parameters WHERE id=1")
                existing = cursor.fetchone()

                if existing:
                    cursor.execute("""
                        UPDATE modem_parameters
                        SET access_token=?, client_id=?, user_name=?, password=?,
                            gsm_modem_mode=?, network_type=?, device_name=?
                        WHERE id=1
                    """, (
                        access_token,
                        client_id,
                        username,
                        password,
                        "esim",
                        "gsm",
                        device_name,
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO modem_parameters
                        VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        access_token,
                        client_id,
                        username,
                        password,
                        "esim",
                        "gsm",
                        device_name,
                    ))

                db.commit()

            finally:
                cursor.close()
                db.close()

        # ethernet or any other case → just redirect back
        return redirect(url_for(redirect_target))

    except Exception as e:
        print("Error:", e)
        return redirect(url_for(redirect_target))

    if "username" not in session:
        return redirect(url_for("login"))

    referrer = request.referrer or ""

    redirect_target = (
        "quick_settings" if "quick_setting" in referrer else "device_credential"
    )

    try:
        sol = request.form.get("solId")

        if sol:
            access_token = request.form.get("access_token")
            client_id = request.form.get("clientId")
            username = request.form.get("user_name")
            password = request.form.get("password")
            device_name = sol

            db = create_connection("modem_config.db")
            if not db:
                return redirect(url_for(redirect_target))

            cursor = db.cursor()
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS modem_parameters (
                        id INTEGER PRIMARY KEY,
                        access_token TEXT,
                        client_id TEXT,
                        user_name TEXT,
                        password TEXT,
                        gsm_modem_mode TEXT,
                        network_type TEXT,
                        device_name TEXT
                    )
                """)

                cursor.execute("SELECT * FROM modem_parameters WHERE id=1")
                existing = cursor.fetchone()

                if existing:
                    cursor.execute("""
                        UPDATE modem_parameters
                        SET access_token=?, client_id=?, user_name=?, password=?,
                            gsm_modem_mode=?, network_type=?, device_name=?
                        WHERE id=1
                    """, (
                        access_token,
                        client_id,
                        username,
                        password,
                        "esim",
                        "gsm",
                        device_name,
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO modem_parameters
                        VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        access_token,
                        client_id,
                        username,
                        password,
                        "esim",
                        "gsm",
                        device_name,
                    ))

                db.commit()

            finally:
                cursor.close()
                db.close()

        # ethernet or any other case ? just redirect back
        return redirect(url_for(redirect_target))

    except Exception as e:
        print("Error:", e)
        return redirect(url_for(redirect_target))



@app.route("/dhcp", methods=["POST"])
def dhcp():
    resetDHCP()
    return redirect(url_for("lan"))


@app.route("/integration_settings")
def integration_settings():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    # ---------- USER ----------
    db_user = create_connection("sepleDB.db")
    cursor_user = db_user.cursor()
    cursor_user.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor_user.fetchone()
    cursor_user.close()
    db_user.close()

    # ---------- DEVICE CONFIG ----------
    db = create_connection("/home/pi/Test3/device_config.db")
    cursor = db.cursor()

    # Safe defaults (VERY IMPORTANT)
    hikvision_nvr_data = {"camera_ip": []}
    hikvision_bacs_data = {"camera_ip": []}
    dahua_nvr_data = {"camera_ip": []}
    cpplus_nvr_data = {"camera_ip": []}
    spars_nvr_data = {"camera_ip": []}

    def load_device(device_type):
        try:
            cursor.execute(
                "SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type=?",
                (device_type,)
            )
            result = cursor.fetchone()

            if not result:
                return {"camera_ip": []}

            camera_ip = result[4]
            if isinstance(camera_ip, str):
                try:
                    camera_ip = json.loads(camera_ip)
                except json.JSONDecodeError:
                    camera_ip = []

            return {
                "ip_address": result[0],
                "username": result[1],
                "password": result[2],
                "port_number": result[3],
                "camera_ip": camera_ip
            }
        except Exception as e:
            print(f"{device_type} ERROR:", e)
            return {"camera_ip": []}

    # ---------- LOAD ALL DEVICES ----------
    hikvision_nvr_data   = load_device("HikvisionNVR1")
    hikvision_bacs_data  = load_device("HikvisionBioMetric1")
    dahua_nvr_data       = load_device("DahuaNVR1")
    cpplus_nvr_data      = load_device("CP_PlusNVR1")
    spars_nvr_data       = load_device("SparshNVR1")  # ✅ FIXED

    cursor.close()
    db.close()

    # ---------- SYSTEM LOGS ----------
    db_logs = create_connection("dexterpanel2.db")
    cursor_logs = db_logs.cursor()
    cursor_logs.execute("SELECT * FROM systemLogs")
    logss_data = cursor_logs.fetchall()
    cursor_logs.close()
    db_logs.close()

    # ---------- RENDER ----------
    return render_template(
        "integrationSettings.html",
        user=user,
        logg=logss_data,

        hikvision_nvr_data=hikvision_nvr_data,
        hikvision_bacs_data=hikvision_bacs_data,
        dahua_nvr_data=dahua_nvr_data,
        cpplus_nvr_data=cpplus_nvr_data,
        spars_nvr_data=spars_nvr_data,

        c1=json.dumps(hikvision_nvr_data["camera_ip"]),
        c2=json.dumps(hikvision_bacs_data["camera_ip"]),
        c3=json.dumps(dahua_nvr_data["camera_ip"]),
        c4=json.dumps(cpplus_nvr_data["camera_ip"]),
        c5=json.dumps(spars_nvr_data["camera_ip"]),
    )

    if "username" in session:
        username = session["username"]
        db = create_connection("/home/pi/Test3/device_config.db")
        db1 = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor1 = db1.cursor()
        cursor1.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        hikvision_nvr_data = None
        hikvision_bacs_data = None
        dahua_nvr_data = None
        cpplus_nvr_data = None
        spars_nvr_data = {"camera_ip": []}

        try:
            # HIKVISION NVR data
            try:
                cursor.execute(
                    "SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type = 'HikvisionNVR1'"
                )
                result = cursor.fetchone()
                print(result)
                if result:
                    # Safely parse camera_ip
                    camera_ip_data = result[4]
                    if isinstance(camera_ip_data, str):
                        try:
                            camera_ip_data = json.loads(camera_ip_data)
                        except json.JSONDecodeError:
                            camera_ip_data = []

                    hikvision_nvr_data = {
                        "ip_address": result[0] ,
                        "port_number": result[3] ,
                        "username": result[1] ,
                        "password": result[2] ,
                        "camera_ip": camera_ip_data
                        
                    }
            except:
                pass

            # HIKVISION BACS data
            try:
                cursor.execute(
                    "SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type = 'HikvisionBioMetric1'"
                )
                result = cursor.fetchone()
                if result:
                    camera_ip_data1 = result[4]
                    if isinstance(camera_ip_data1, str):
                        try:
                            camera_ip_data1 = json.loads(camera_ip_data1)
                        except json.JSONDecodeError:
                            camera_ip_data1 = []
                    hikvision_bacs_data = {
                        "ip_address": result[0],
                        "port_number": result[3] ,
                        "username": result[1] ,
                        "password": result[2] ,
                        "camera_ip": camera_ip_data1
                        
                    }
                    
            except:
                pass

            # DAHUA NVR data
            try:
                cursor.execute(
                    "SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type = 'DahuaNVR1'"
                )
                result = cursor.fetchone()
                if result:
                    camera_ip_data2 = result[4]
                    if isinstance(camera_ip_data2, str):
                        try:
                            camera_ip_data2 = json.loads(camera_ip_data2)
                        except json.JSONDecodeError:
                            camera_ip_data2 = []
                    dahua_nvr_data = {
                        "ip_address": result[0] ,
                        "port_number": result[3],
                        "username": result[1] ,
                        "password": result[2] ,
                        "camera_ip": camera_ip_data2
                        
                    }
                    print("niyat Kharaab", dahua_nvr_data)
            except:
                pass

            ## CPPLUS NVR DATA
            try:
                cursor.execute("SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type = 'CP_PlusNVR1'")
                result= cursor.fetchone()
                if result:
                    camera_ip_data3 =result[4]
                    if isinstance(camera_ip_data3,str):
                        try:
                            camera_ip_data3= json.loads(camera_ip_data3)
                        except json.JSONDecodeError:
                            camera_ip_data3 = []
                    cpplus_nvr_data ={
                        "ip_address": result[0],
                        "port_number": result[3],
                        "username": result[1],
                        "password": result[2],
                        "camera_ip": camera_ip_data3
                    }
            except:
                pass

            ## SPARSH NVR DATA
            try:
                cursor.execute("SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type = 'SparshNVR1'")
                result.fetchone()
                if result:
                    camera_ip_data4 = result[4]
                    if isinstance(camera_ip_data4, str):
                        try:
                            camera_ip_data4 = json.loads(camera_ip_data4)
                        except json.JSONDecodeError:
                            camera_ip_data4 = []
                    spars_nvr_data = {
                        "ip_address": result[0],
                        "port_number": result[3],
                        "username": result[1],
                        "password": result[2],
                        "camera_ip": camera_ip_data4
                    }
            except:
                pass


    

        except:
            pass

        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        return render_template(
            "integrationSettings.html",
            logg=logss_data,
            user=user,
            hikvision_nvr_data=hikvision_nvr_data,
            hikvision_bacs_data=hikvision_bacs_data,
            dahua_nvr_data=dahua_nvr_data,
            cpplus_nvr_data=cpplus_nvr_data,
            spars_nvr_data=spars_nvr_data,
            c1=json.dumps(hikvision_nvr_data["camera_ip"]),
            c2=json.dumps(hikvision_bacs_data["camera_ip"]),
            c3=json.dumps(dahua_nvr_data["camera_ip"]),
            c4=json.dumps(cpplus_nvr_data["camera_ip"]),
            c5=json.dumps(spars_nvr_data["camera_ip"]),
        )  # <--- this will be list now
    # print(f"{hikvision_nvr_data['camera_ip']}//{hikvision_bacs_data['camera_ip']}//{dahua_nvr_data['camera_ip']}")
    return redirect(url_for("login"))
    if "username" in session:
        username = session["username"]
        db = create_connection("/home/pi/Test3/device_config.db")
        db1 = create_connection("sepleDB.db")
        cursor = db.cursor()
        cursor1 = db1.cursor()
        cursor1.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()

        hikvision_nvr_data = None
        hikvision_bacs_data = None
        dahua_nvr_data = None
        cpplus_nvr_data = None
        spars_nvr_data = {"camera_ip": []}

        try:
            # HIKVISION NVR data
            try:
                cursor.execute(
                    "SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type = 'HikvisionNVR1'"
                )
                result = cursor.fetchone()
                print(result)
                if result:
                    # Safely parse camera_ip
                    camera_ip_data = result[4]
                    if isinstance(camera_ip_data, str):
                        try:
                            camera_ip_data = json.loads(camera_ip_data)
                        except json.JSONDecodeError:
                            camera_ip_data = []

                    hikvision_nvr_data = {
                        "ip_address": result[0] ,
                        "port_number": result[3] ,
                        "username": result[1] ,
                        "password": result[2] ,
                        "camera_ip": camera_ip_data
                        
                    }
            except:
                pass

            # HIKVISION BACS data
            try:
                cursor.execute(
                    "SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type = 'HikvisionBioMetric1'"
                )
                result = cursor.fetchone()
                if result:
                    camera_ip_data1 = result[4]
                    if isinstance(camera_ip_data1, str):
                        try:
                            camera_ip_data1 = json.loads(camera_ip_data1)
                        except json.JSONDecodeError:
                            camera_ip_data1 = []
                    hikvision_bacs_data = {
                        "ip_address": result[0],
                        "port_number": result[3] ,
                        "username": result[1] ,
                        "password": result[2] ,
                        "camera_ip": camera_ip_data1
                        
                    }
                    
            except:
                pass

            # DAHUA NVR data
            try:
                cursor.execute(
                    "SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type = 'DahuaNVR1'"
                )
                result = cursor.fetchone()
                if result:
                    camera_ip_data2 = result[4]
                    if isinstance(camera_ip_data2, str):
                        try:
                            camera_ip_data2 = json.loads(camera_ip_data2)
                        except json.JSONDecodeError:
                            camera_ip_data2 = []
                    dahua_nvr_data = {
                        "ip_address": result[0] ,
                        "port_number": result[3],
                        "username": result[1] ,
                        "password": result[2] ,
                        "camera_ip": camera_ip_data2
                        
                    }
                    print("niyat Kharaab", dahua_nvr_data)
            except:
                pass

            ## CPPLUS NVR DATA
            try:
                cursor.execute("SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type = 'CP_PlusNVR1'")
                result= cursor.fetchone()
                if result:
                    camera_ip_data3 =result[4]
                    if isinstance(camera_ip_data3,str):
                        try:
                            camera_ip_data3= json.loads(camera_ip_data3)
                        except json.JSONDecodeError:
                            camera_ip_data3 = []
                    cpplus_nvr_data ={
                        "ip_address": result[0],
                        "port_number": result[3],
                        "username": result[1],
                        "password": result[2],
                        "camera_ip": camera_ip_data3
                    }
            except:
                pass

            ## SPARSH NVR DATA
            try:
                cursor.execute("SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type = 'SparshNVR1'")
                result.fetchone()
                if result:
                    camera_ip_data4 = result[4]
                    if isinstance(camera_ip_data4, str):
                        try:
                            camera_ip_data4 = json.loads(camera_ip_data4)
                        except json.JSONDecodeError:
                            camera_ip_data4 = []
                    spars_nvr_data = {
                        "ip_address": result[0],
                        "port_number": result[3],
                        "username": result[1],
                        "password": result[2],
                        "camera_ip": camera_ip_data4
                    }
            except:
                pass


    

        except:
            pass

        cursor.close()
        db.close()

        db3 = create_connection("dexterpanel2.db")
        cursor3 = db3.cursor()
        cursor3.execute("SELECT * FROM systemLogs")
        logss_data = cursor3.fetchall()
        cursor3.close()
        db3.close()

        return render_template(
            "integrationSettings.html",
            logg=logss_data,
            user=user,
            hikvision_nvr_data=hikvision_nvr_data,
            hikvision_bacs_data=hikvision_bacs_data,
            dahua_nvr_data=dahua_nvr_data,
            cpplus_nvr_data=cpplus_nvr_data,
            spars_nvr_data=spars_nvr_data,
            c1=json.dumps(hikvision_nvr_data["camera_ip"]),
            c2=json.dumps(hikvision_bacs_data["camera_ip"]),
            c3=json.dumps(dahua_nvr_data["camera_ip"]),
            c4=json.dumps(cpplus_nvr_data["camera_ip"]),
            c5=json.dumps(spars_nvr_data["camera_ip"]),
        )  # <--- this will be list now
    # print(f"{hikvision_nvr_data['camera_ip']}//{hikvision_bacs_data['camera_ip']}//{dahua_nvr_data['camera_ip']}")
    return redirect(url_for("login"))


# @app.route('/save_camera_integration', methods=['POST'])
# def save_camera_integration():
#     if 'username' not in session:
#         return redirect(url_for('login'))

#     form_data = request.form  # Use this for form data
#     camera_map = {}

#     for key, value in form_data.items():
#         if key.startswith("camera_"):
#             parts = key.split("_")
#             index = parts[1]
#             field = parts[2]
#             if index not in camera_map:
#                 camera_map[index] = {}
#             camera_map[index][field] = value

#     result = [camera_map[i] for i in sorted(camera_map.keys(), key=int)]

#     for i in result:
#         device_type = i['type']
#         cameraIp = {
#             "ip_address": i['ip'],
#             "username": i['username'],
#             "password": i['password']
#         }

#         db = create_connection("device_config.db")
#         cursor = db.cursor()
#         cursor.execute('''UPDATE device_parameters set camera_ip=? WHERE device_type=? ''',(cameraIp,device_type))
#         db.commit()
#         cursor.close()
#         db.close()
#     return result


@app.route("/senddata", methods=["POST"])
def sendata():
    data = request.form.to_dict()
    print(data)  # Now this will print the actual key-value pairs
    return jsonify(data)


from flask import request, redirect, url_for, session

@app.route("/save_integration_hiknvr", methods=["POST"])
def save_integration_hiknvr():
    if "username" not in session:
        return redirect(url_for("login"))

    try:
        device_type = request.form.get("device_type_d")
        ip_address = request.form.get("ip_address")
        username = request.form.get("username")
        password = request.form.get("password")
        port_number = request.form.get("port_number")
        camera_ip = request.form.get("cameras_json")

        db = create_connection("/home/pi/Test3/device_config.db")
        if not db:
            return redirect(url_for("integration_settings"))

        cursor = db.cursor()

        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS device_parameters(
                    id INTEGER PRIMARY KEY,
                    device_type TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT,
                    port TEXT,
                    camera_ip JSON
                )
            """)

            cursor.execute(
                "SELECT 1 FROM device_parameters WHERE device_type=?",
                (device_type,)
            )
            existing = cursor.fetchone()

            if existing:
                cursor.execute(
                    """
                    UPDATE device_parameters
                    SET ip_address=?, username=?, password=?, port=?, camera_ip=?
                    WHERE device_type=?
                    """,
                    (ip_address, username, password, port_number, camera_ip, device_type)
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO device_parameters
                    (device_type, ip_address, username, password, port, camera_ip)
                    VALUES (?,?,?,?,?,?)
                    """,
                    (device_type, ip_address, username, password, port_number, camera_ip)
                )

            db.commit()

        finally:
            cursor.close()
            db.close()

    except Exception as e:
        print("Save error:", e)
        return redirect(url_for("integration_settings"))

    # 🔥 SMART REDIRECT BASED ON SOURCE PAGE
    referrer = request.referrer or ""

    if "quick_setting" in referrer:
        return redirect(url_for("quick_settings"))
    elif "integration_setting" in referrer:
        return redirect(url_for("integration_settings"))

    # fallback
    return redirect(url_for("integration_settings"))

    if "username" not in session:
        return redirect(url_for("login"))

    data = None

    try:
        device_type = request.form.get("device_type_d")
        ip_address = request.form.get("ip_address")
        username = request.form.get("username")
        password = request.form.get("password")
        port_number = request.form.get("port_number")
        camera_ip = request.form.get("cameras_json")

        db = create_connection("/home/pi/Test3/device_config.db")
        if not db:
            # print("no db")
            return redirect(url_for("integration_settings"))

        cursor = db.cursor()

        try:
            # Create table
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS device_parameters(
                    id INTEGER PRIMARY KEY,
                    device_type TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT,
                    port TEXT,
                    camera_ip json
                   
                )
            """
            cursor.execute(create_table_sql)

            # Check if record exists
            cursor.execute(
                "SELECT * FROM device_parameters WHERE device_type=?", (device_type,)
            )

            existing = cursor.fetchone()

            print(existing)

            if existing:
                update_sql = "UPDATE device_parameters SET ip_address=?, username=?, password=?, port=?, camera_ip=? WHERE device_type=?"
                cursor.execute(
                    update_sql,
                    (
                        ip_address,
                        username,
                        password,
                        port_number,
                        camera_ip,
                        device_type,
                    ),
                )
                print(device_type,camera_ip,"avdiaoidoadhoa")      
            else:
                insert_sql = "INSERT INTO device_parameters (device_type, ip_address, username, password, port,camera_ip) VALUES (?,?,?,?,?,?)"
                cursor.execute(
                    insert_sql,
                    (
                        device_type,
                        ip_address,
                        username,
                        password,
                        port_number,
                        camera_ip,
                    ),
                )

            db.commit()

        except:
            print("error")
            return redirect(url_for("integration_settings"))

        finally:
            cursor.close()
            db.close()

    except:
        return redirect(url_for("integration_settings"))

    return redirect(url_for("quick_settings"))

    if "username" not in session:
        return redirect(url_for("login"))

    data = None

    try:
        device_type = request.form.get("device_type_d")
        ip_address = request.form.get("ip_address")
        username = request.form.get("username")
        password = request.form.get("password")
        port_number = request.form.get("port_number")
        camera_ip = request.form.get("cameras_json")

        db = create_connection("/home/pi/Test3/device_config.db")
        if not db:
            # print("no db")
            return redirect(url_for("integration_settings"))

        cursor = db.cursor()

        try:
            # Create table
            create_table_sql = """
                CREATE TABLE IF NOT EXISTS device_parameters(
                    id INTEGER PRIMARY KEY,
                    device_type TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT,
                    port TEXT,
                    camera_ip json
                   
                )
            """
            cursor.execute(create_table_sql)

            # Check if record exists
            cursor.execute(
                "SELECT * FROM device_parameters WHERE device_type=?", (device_type,)
            )

            existing = cursor.fetchone()

            print(existing)

            if existing:
                update_sql = "UPDATE device_parameters SET ip_address=?, username=?, password=?, port=?, camera_ip=? WHERE device_type=?"
                cursor.execute(
                    update_sql,
                    (
                        ip_address,
                        username,
                        password,
                        port_number,
                        camera_ip,
                        device_type,
                    ),
                )
                print(device_type,camera_ip,"avdiaoidoadhoa")      
            else:
                insert_sql = "INSERT INTO device_parameters (device_type, ip_address, username, password, port,camera_ip) VALUES (?,?,?,?,?,?)"
                cursor.execute(
                    insert_sql,
                    (
                        device_type,
                        ip_address,
                        username,
                        password,
                        port_number,
                        camera_ip,
                    ),
                )

            db.commit()

        except:
            print("error")
            return redirect(url_for("integration_settings"))

        finally:
            cursor.close()
            db.close()

    except:
        return redirect(url_for("integration_settings"))

    return redirect(url_for("integration_settings"))



#new add on quick setting it's a combination of output management, active integration abnd device credential.
@app.route("/quick_settings")
def quick_settings():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    # ---------------- USER ----------------
    db = create_connection("sepleDB.db")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    # ---------------- LOGS ----------------
    db3 = create_connection("dexterpanel2.db")
    cursor3 = db3.cursor()
    cursor3.execute("SELECT * FROM systemLogs")
    logss_data = cursor3.fetchall()
    cursor3.close()
    db3.close()

    # ---------------- eSIM DATA ----------------
    mpdata = {"clintId": "", "userName": "", "Pass": "", "dvName": ""}
    try:
        db2 = create_connection("/home/pi/Test3/modem_config.db")
        cursor2 = db2.cursor()
        cursor2.execute("SELECT * FROM modem_parameters WHERE id=1")
        m = cursor2.fetchone()
        if m:
            mpdata = {
                "clintId": m[2],
                "userName": m[3],
                "Pass": m[4],
                "dvName": m[7]
            }
        cursor2.close()
        db2.close()
    except:
        pass

    # ---------------- DEVICE INTEGRATIONS ----------------
    def get_device(device_type):
        try:
            db = create_connection("/home/pi/Test3/device_config.db")
            cursor = db.cursor()
            cursor.execute(
                "SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type=?",
                (device_type,)
            )
            r = cursor.fetchone()
            cursor.close()
            db.close()

            if r:
                camera_ip = json.loads(r[4]) if r[4] else []
                return {
                    "ip_address": r[0],
                    "username": r[1],
                    "password": r[2],
                    "port_number": r[3],
                    "camera_ip": camera_ip
                }
        except:
            pass

        return {
            "ip_address": "",
            "username": "",
            "password": "",
            "port_number": "",
            "camera_ip": []
        }

    hikvision_nvr_data  = get_device("HikvisionNVR1")
    hikvision_bacs_data = get_device("HikvisionBioMetric1")
    dahua_nvr_data      = get_device("DahuaNVR1")
    cpplus_nvr_data     = get_device("CP_PlusNVR1")
    spars_nvr_data      = get_device("SparshNVR1")

    # ---------------- CAMERA JSON (JS SAFE) ----------------
    c1 = json.dumps(hikvision_nvr_data["camera_ip"])
    c2 = json.dumps(hikvision_bacs_data["camera_ip"])
    c3 = json.dumps(dahua_nvr_data["camera_ip"])
    c4 = json.dumps(cpplus_nvr_data["camera_ip"])
    c5 = json.dumps(spars_nvr_data["camera_ip"])

    return render_template(
        "quick_settings.html",
        user=user,
        logg=logss_data,
        mpdata=mpdata,
        hikvision_nvr_data=hikvision_nvr_data,
        hikvision_bacs_data=hikvision_bacs_data,
        dahua_nvr_data=dahua_nvr_data,
        cpplus_nvr_data=cpplus_nvr_data,
        spars_nvr_data=spars_nvr_data,
        c1=c1, c2=c2, c3=c3, c4=c4, c5=c5
    )

    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    # ---------- USER ----------
    db = create_connection("sepleDB.db")
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    # ---------- SYSTEM LOGS ----------
    db3 = create_connection("dexterpanel2.db")
    cursor3 = db3.cursor()
    cursor3.execute("SELECT * FROM systemLogs")
    logs = cursor3.fetchall()
    cursor3.close()
    db3.close()

    # ---------- DEVICE CREDENTIAL ----------
    mpdata = None
    db2 = create_connection("/home/pi/Test3/modem_config.db")
    cursor2 = db2.cursor()
    cursor2.execute("SELECT * FROM modem_parameters")
    m = cursor2.fetchone()
    if m:
        mpdata = {
            "clientId": m[2],
            "userName": m[3],
            "password": m[4],
            "deviceName": m[7],
        }
    cursor2.close()
    db2.close()

    # ---------- INTEGRATION SETTINGS ----------
    integration_data = {}
    db4 = create_connection("/home/pi/Test3/device_config.db")
    cursor4 = db4.cursor()

    def fetch_device(device_type):
        cursor4.execute(
            "SELECT ip_address, username, password, port, camera_ip FROM device_parameters WHERE device_type=?",
            (device_type,)
        )
        row = cursor4.fetchone()
        if not row:
            return None
        try:
            camera_ip = json.loads(row[4]) if row[4] else []
        except:
            camera_ip = []
        return {
            "ip": row[0],
            "username": row[1],
            "password": row[2],
            "port": row[3],
            "camera_ip": camera_ip
        }

    integration_data["hikvision"] = fetch_device("HikvisionNVR1")
    integration_data["dahua"] = fetch_device("DahuaNVR1")
    integration_data["cpplus"] = fetch_device("CP_PlusNVR1")

    cursor4.close()
    db4.close()

    return render_template(
        "quick_settings.html",
        user=user,
        logs=logs,
        mpdata=mpdata,
        integration=integration_data
    )


if __name__ == "__main__":
    # Initialize default users in database
    initialize_users()
    app.run(debug=True, host="0.0.0.0", port=5001, threaded=True)
    
