# Dexter HMS Web Server — Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Architecture Pattern](#architecture-pattern)
4. [Entry Points & Server Startup](#entry-points--server-startup)
5. [Configuration](#configuration)
6. [Authentication & Authorization](#authentication--authorization)
7. [Database Layer](#database-layer)
8. [Routes & Endpoints](#routes--endpoints)
9. [Middleware](#middleware)
10. [Templates & Frontend](#templates--frontend)
11. [Service Modules](#service-modules)
12. [Hardware Integrations](#hardware-integrations)
13. [MQTT & IoT Connectivity](#mqtt--iot-connectivity)
14. [Dependencies](#dependencies)
15. [Data Flow](#data-flow)
16. [Request Lifecycle](#request-lifecycle)
17. [Deployment](#deployment)

---

## Overview

**Dexter HMS (Home Management System)** is a Flask-based web server designed to run on a Raspberry Pi. It acts as a local management interface for an IoT/embedded device, providing:

- Device configuration (LAN, GSM/GNSS modem, eSIM, zones)
- User authentication with role-based access control
- Camera/NVR integration (Hikvision, Dahua, CP+)
- MQTT and ThingsBoard connectivity
- Over-The-Air (OTA) firmware updates
- System monitoring (CPU, memory, disk, network)
- Event and system logging

| Property | Value |
|---|---|
| Language | Python 3 |
| Web Framework | Flask 2.2.5 |
| Database | SQLite (7 separate `.db` files) |
| Exposed Port | 5001 (all network interfaces) |
| Architecture | Monolithic MVC |
| Main Source File | `seple.py` (≈3 878 lines) |
| Total API Endpoints | 84 |
| HTML Templates | 28 |
| Service/Utility Modules | 40+ |
| Frontend Approach | Server-side rendering (Jinja2) + AJAX |

---

## Directory Structure

```
Dexter---webserver/
├── seple.py                            # Primary Flask application (~3 878 lines)
├── updated_seple.py                    # Alternate/updated version (~2 145 lines)
├── main2.py                            # Secondary main file
├── sepletest.py                        # Ad-hoc test file
├── requirements.txt                    # Python dependency list
├── webserver_V3_integration.sh         # Startup shell script
├── README.md                           # Project readme
│
├── templates/                          # Jinja2 HTML templates (28 files)
│   ├── login.html
│   ├── home.html
│   ├── general.html
│   ├── device_config.html
│   ├── connectivity_settings.html
│   ├── integration_settings.html
│   ├── logs.html
│   ├── reports.html
│   ├── maintenance.html
│   ├── system_test.html / system _test_try.html
│   └── … (20 more templates)
│
├── static/
│   ├── css/                            # 24 stylesheet files
│   ├── js/                             # 6 JavaScript files
│   │   ├── system_test.js
│   │   └── log_test.js
│   └── asset/                          # Images and other static assets
│
├── Test3_V1.0_PrintOff/                # 40+ service/utility Python modules
│   ├── SDL_DS1307.py                   # Real-Time Clock interface
│   ├── Lan_setting.py                  # LAN configuration helpers
│   ├── DeviceProvisioning_Module.py    # Device provisioning
│   ├── TLChronosProMAIN_391.py         # Main system control
│   ├── database_handler.py             # Database operations wrapper
│   ├── network_info.py / getNetworkInfo.py
│   ├── Configure_Network_7.py
│   ├── Lan_Info_Collector_2.py
│   ├── device_parameters_module.py
│   ├── logical_params_module.py
│   ├── json_db_module.py
│   ├── buffer_manager.py
│   ├── SerialCommunication.py
│   ├── thingsboard_mqtt_publisher.py
│   ├── dahua_nvr_dvr_get_store_json_7i.py
│   ├── dahua_RTC_sync.py
│   ├── hik_RTC_sync.py
│   ├── hikvision1_biometric_14.py
│   ├── nvr_dvr_bacs_integration_9.py
│   ├── Extract_Logs_Dahua_41.py
│   ├── Hik_SD_Card_REC_Cam_Info_Status_int.py
│   ├── Dahua_Recording_SD_Card_Cam_Info_Status_int.py
│   ├── ota2.py / netota.py             # OTA update modules
│   ├── shiftRegister.py                # GPIO shift register
│   ├── Adafruit_CharLCD.py             # LCD display driver
│   ├── serial_data_logger.py
│   ├── clear_all_data.py
│   ├── reset_to_dhcp.py
│   ├── externalDeviceConfig.py
│   └── testsqlite3_2f.py               # SQLite unit tests
│
├── SDL_Pi_TCA9545/                     # I²C GPIO multiplexer module
│
└── SQLite databases (runtime, not versioned):
    ├── sepleDB.db                      # Main application database
    ├── dexterpanel2.db                 # System logs
    ├── device_config.db                # Device parameters
    ├── modem_config.db                 # Modem / MQTT credentials
    ├── active_integration.db           # Active integration state
    ├── logical_params_active_integration.db
    └── securelink.db                   # Secure link configuration
```

---

## Architecture Pattern

The application follows a **Monolithic MVC (Model-View-Controller)** pattern hosted as a single Python process.

```
┌─────────────────────────────────────────────────────────┐
│                     Browser / API Client                 │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP (port 5001)
┌──────────────────────────▼──────────────────────────────┐
│                       Flask App (seple.py)               │
│  ┌────────────┐   ┌───────────────┐   ┌──────────────┐  │
│  │ Middleware │   │  Controllers  │   │    Views     │  │
│  │ (headers, │──▶│ (84 routes)   │──▶│ (28 Jinja2   │  │
│  │  session) │   │               │   │  templates)  │  │
│  └────────────┘   └──────┬────────┘   └──────────────┘  │
│                          │                               │
│                  ┌───────▼────────┐                      │
│                  │   SQLite DBs   │                      │
│                  │ (7 databases)  │                      │
│                  └───────────────┘                      │
│                          │                               │
│                  ┌───────▼────────────────────────┐      │
│                  │   Service Modules (40+ files)  │      │
│                  │  LAN · GSM · OTA · MQTT · NVR  │      │
│                  └────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
              │                        │
   ┌──────────▼──────────┐   ┌─────────▼──────────┐
   │  Hardware (GPIO,    │   │  External Services  │
   │  Serial, RTC, LCD)  │   │  (ThingsBoard MQTT, │
   └─────────────────────┘   │  Hikvision, Dahua)  │
                             └────────────────────┘
```

### Design Patterns in Use

| Pattern | Where used |
|---|---|
| **Singleton** | Single Flask `app` instance |
| **Factory** | `create_connection(db_file)` creates DB connections |
| **Middleware / Decorator** | `@app.after_request` for cache-control headers |
| **Strategy** | Pluggable integration handlers (Hikvision, Dahua, CP+, etc.) |
| **Observer** | Event logging to `systemLogs` on significant actions |
| **Template Method** | All protected routes share the same session-check pattern |

---

## Entry Points & Server Startup

### Shell Script (`webserver_V3_integration.sh`)

```bash
#!/bin/bash
/usr/bin/python3 /home/pi/Test3/webserver/seple.py &
wait
```

Starts the Flask server as a background process.

### Python Startup Sequence (`seple.py`)

```
1. time.sleep(59)          # Wait for OS/hardware to initialise
2. SDL_DS1307()            # Initialise the Real-Time Clock
3. app = Flask(__name__)   # Create the Flask application
4. app.secret_key = "SEPLe"
5. app.permanent_session_lifetime = timedelta(minutes=30)
6. initialize_users()      # Seed default users into sepleDB.db
7. app.run(debug=True, host="0.0.0.0", port=5001, threaded=True)
```

### Shutdown / Reboot

Two `threading.Timer` operations handle graceful shutdown:

| Function | Delay | Action |
|---|---|---|
| `reboot_rpi()` | 30 s | Reboots the Raspberry Pi (`os.system("sudo reboot")`) |
| `terminate_server()` | 1 s | Terminates the Flask process |

---

## Configuration

All configuration is **hardcoded** — no external `.env` or config files are used.

| Parameter | Value | Location |
|---|---|---|
| Flask secret key | `"SEPLe"` | `seple.py` |
| Master password | `"SEPLe@1984"` | `seple.py` |
| Server host | `0.0.0.0` | `seple.py` |
| Server port | `5001` | `seple.py` |
| Session timeout | 30 minutes | `seple.py` |
| Admin password file | `/home/pi/TLChronosPro/AdminPass.txt` | `seple.py` |
| Default MQTT access token | `6dNkl093nG4HvksMmYDD` | `DeviceProvisioning_Module.py` |
| Default MQTT client ID | `pt2gv4dhnol87qgt2lyw` | `DeviceProvisioning_Module.py` |
| Default device name | `Dexter-HMS` | `DeviceProvisioning_Module.py` |
| Default network type | ethernet | `DeviceProvisioning_Module.py` |

---

## Authentication & Authorization

### Authentication

- **Method:** Flask session-based authentication (no JWT / OAuth)
- **Credentials stored:** `users` table in `sepleDB.db` (plain-text password in SQLite)
- **Two roles:** `user` and `site_engineer`

**Login flow:**

```
POST /login
  ├── Read username, password, user_type from form
  ├── site_engineer + password == MASTER_PASSWORD
  │     └── Grant access, set session["master_login"] = True
  ├── Regular path: SELECT * FROM users WHERE username=? AND password=? AND user_type=?
  │     └── Match found → set session["username"], session["user_type"]
  └── No match → redirect /login with error message
```

### Session Variables

| Variable | Type | Description |
|---|---|---|
| `session["username"]` | string | Logged-in username |
| `session["user_type"]` | string | `"user"` or `"site_engineer"` |
| `session["master_login"]` | bool | True when master password was used |

### Authorization

```python
def check_user_access(required_permissions):
    user_type = session.get("user_type")
    if user_type == "site_engineer":
        return True          # full access
    return user_type in required_permissions
```

All protected routes check for `"username"` in the session before processing. Restricted pages (provisioning, LAN settings, device credentials) require `site_engineer`.

### Default Users (seeded by `initialize_users()`)

| Username | Role |
|---|---|
| `admin` | `site_engineer` |
| `user` | `user` |

---

## Database Layer

### Connection Factory

```python
def create_connection(db_file):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, db_file)
    conn = sqlite3.connect(db_path)
    return conn
```

Connections are opened **per-request** and closed after each operation (no connection pooling).

### Databases and Tables

#### `sepleDB.db` — Main Application Database

| Table | Key Columns | Purpose |
|---|---|---|
| `users` | id, username, password, user_type | User accounts & authentication |
| `zone` | zoneId, activated, selectedDevice, buzzerStatus | Security zone configuration |
| `powerzone` | zoneId, activated, selectedDevice, buzzerStatus | Power zone configuration |
| `general` | brand_name, site_name, ID | Site-level branding/info |
| `lan` | set_ip_address, set_port_no, subnet_mask, gate_way, dns_setups, apn_settings, network_led_sts, wireless_lan, ip_module, static_or_dynamic, ID | LAN interface configuration |
| `gsm` | ID, gsm_activated | GSM modem activation state |
| `gnss` | ID, gnss_activated | GNSS/GPS activation state |
| `eSim` | eSim_activated, select_network, ID | eSIM configuration |
| `deviceCredential` | — | Device-level credentials |
| `provision` | — | Device provisioning data |
| `integration_config` | — | General integration settings |
| `hikvision_nvr_integration` | — | Hikvision NVR parameters |
| `hikvision_bacs_integration` | — | Hikvision BACS parameters |
| `dahua_nvr_integration` | — | Dahua NVR parameters |
| `device_credentials` | — | Additional device credentials |

#### `dexterpanel2.db` — Logging Database

| Table | Key Columns | Purpose |
|---|---|---|
| `systemLogs` | deviceType, logType, rtcYear, rtcMonth, rtcDate, rtcHour, rtcMinute, rtcSecound | Timestamped system event log |
| `camera_integrations` | id, ip_address, username, password, created_at, updated_at | Camera integration records |

#### Other Databases

| File | Purpose |
|---|---|
| `device_config.db` | Device hardware parameters |
| `modem_config.db` | MQTT credentials and modem parameters |
| `active_integration.db` | Active integration state |
| `logical_params_active_integration.db` | Logical parameters for active integrations |
| `securelink.db` | Secure link / X.509 certificate configuration |

---

## Routes & Endpoints

All routes are defined in `seple.py`. Routes use standard Flask decorators and accept `GET`, `POST`, or `PUT` methods.

### Authentication

| Method | Path | Description |
|---|---|---|
| GET, POST | `/login` | Login page and form handler |
| GET, POST | `/resetpassword` | Password reset |
| GET | `/logout` | Clear session and redirect to login |

### Dashboard & Home

| Method | Path | Description |
|---|---|---|
| GET | `/` | Root — redirects based on session |
| GET | `/home` | Main dashboard (session required) |
| GET | `/stats` | Live system stats: CPU, memory, disk, network, uptime |

### System Configuration

| Method | Path | Description |
|---|---|---|
| GET | `/general` | General settings page |
| POST | `/date_time` | Update system date/time |
| POST | `/brandname` | Update brand name |
| GET, POST | `/general_data` | Read/write general site data |
| GET | `/advanced` | Advanced settings page |
| GET | `/quick_settings` | Quick settings page |

### Device Configuration

| Method | Path | Description |
|---|---|---|
| GET | `/device_config` | Device configuration page |
| GET, PUT | `/get_zone` | Get zone configuration |
| PUT | `/update_zone` | Update a zone |
| GET | `/powerzone_config` | Power zone settings page |
| GET, PUT | `/get_powerzone` | Get/update power zone |
| PUT | `/power_zone` | Write power zone data |
| POST | `/control` | Device control command |

### Network & LAN

| Method | Path | Description |
|---|---|---|
| GET | `/lan` | LAN configuration page |
| POST | `/data_lan` | Create/update LAN settings |
| PUT | `/data2_lan` | Partial LAN update |
| GET | `/get_data2lan` | Retrieve LAN data |
| POST | `/dhcp` | Apply/reset DHCP |
| GET | `/connectivity_settings` | Network connectivity overview |
| POST | `/connectivity_settings` | Update connectivity settings |

### Modem & Wireless

| Method | Path | Description |
|---|---|---|
| GET | `/net_gsm` | GSM settings page |
| GET | `/get_gsm` | Get GSM data |
| PUT | `/netdata_gsm` | Update GSM data |
| GET | `/gnss` | GNSS settings page |
| GET | `/get_gnss` | Get GNSS data |
| PUT | `/net_gnss` | Update GNSS data |
| GET | `/get_eSim` | Get eSIM data |
| PUT | `/neteSim_data` | Update eSIM data |

### Security & Credentials

| Method | Path | Description |
|---|---|---|
| GET | `/device_credential` | Device credentials page |
| POST | `/device_credentials` | Update device credentials |

### Device Management

| Method | Path | Description |
|---|---|---|
| GET | `/device_management` | Device management overview |
| GET, POST | `/provision` | Provisioning page and form handler |
| POST | `/setprovisiondevice` | Set provisioning device |
| GET | `/protocol_config` | Protocol configuration |
| GET | `/OTA` | Over-The-Air updates page |

### Integrations

| Method | Path | Description |
|---|---|---|
| GET | `/output_controls` | Output control panel |
| GET | `/integration_settings` | Integration settings overview |
| GET | `/get_activeIntegration` | Get active integration list |
| PUT | `/data_active_integration` | Update active integration |
| GET | `/get_active_integration_hikvidion` | Hikvision NVR integration data |
| PUT | `/data_active_integration_hikvidion` | Update Hikvision NVR |
| GET | `/get_active_integration_dh` | Dahua NVR data |
| PUT | `/data_active_integration_dh` | Update Dahua NVR |
| GET | `/get_active_integration_ac` | Access Control integration |
| PUT | `/data_active_integration_ac` | Update Access Control |
| GET | `/get_active_integration_cp` | CP Plus NVR data |
| PUT | `/data_active_integration_cp` | Update CP Plus NVR |
| GET | `/get_active_integration_sp` | Security Provider data |
| PUT | `/data_active_integration_sp` | Update Security Provider |

### Connectivity / Cloud

| Method | Path | Description |
|---|---|---|
| GET | `/connection` | Cloud connection settings |
| POST | `/acces_token` | Configure MQTT access token |
| POST | `/x509` | Upload/configure X.509 certificate |
| POST | `/mqtt_basic` | Configure MQTT basic credentials |

### Data & Logging

| Method | Path | Description |
|---|---|---|
| GET | `/logs` | System logs page |
| GET | `/delete` | Clear all logs |
| GET | `/reports` | Reports page |
| POST | `/senddata` | Send telemetry data |
| GET, POST | `/send_data` | Send data (endpoint 1) |
| GET, POST | `/send_data2` | Send data (endpoint 2) |

### System Operations

| Method | Path | Description |
|---|---|---|
| POST | `/restart` | Reboot the Raspberry Pi |
| POST | `/terminate` | Shut down the Flask server |

### Maintenance & Misc

| Method | Path | Description |
|---|---|---|
| GET | `/maintenance` | Maintenance page |
| GET | `/system_test` | System self-test page |
| GET | `/SOL` | SOL (Serial over LAN) configuration |
| GET | `/come_soon` | Coming soon placeholder |

---

## Middleware

### Cache-Control Headers

Applied to every response via `@app.after_request`:

```python
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
```

Prevents browsers from caching sensitive management pages.

### Session Management

- **Secret key:** `"SEPLe"`
- **Lifetime:** 30 minutes (`app.permanent_session_lifetime = timedelta(minutes=30)`)
- Uses Flask's built-in signed cookie sessions.

### Flask Extensions Loaded

| Extension | Purpose |
|---|---|
| `Flask-Cors` | Cross-Origin Resource Sharing |
| `Flask-WTF` | WTForm integration / CSRF protection |
| `Flask-Mail` | Email sending |
| `Flask-SQLAlchemy` | ORM (imported but SQLite accessed directly) |
| `flask-talisman` | HTTP security headers |

---

## Templates & Frontend

### Template Engine

Jinja2 (bundled with Flask). Templates are stored in `/templates/`.

### Frontend Architecture

- **No JavaScript framework** — plain HTML, CSS, and vanilla JavaScript.
- Dynamic data is loaded via **AJAX (XMLHttpRequest / fetch)** calls to the Flask JSON endpoints.
- CSS is organised into per-page stylesheets under `static/css/`.

### Request/Response for UI Pages

```
Browser GET /home
  └─ Flask route handler
       └─ render_template("home.html", **context)
            └─ Jinja2 renders HTML with injected data
                 └─ HTML returned to browser
```

### AJAX Pattern (configuration updates)

```
User edits a field → JavaScript captures change
  └─ fetch("PUT /get_zone", { body: JSON.stringify(data) })
       └─ Flask route updates SQLite
            └─ Returns JSON { "status": "ok" }
                 └─ JavaScript shows success/error feedback
```

---

## Service Modules

All service modules live under `Test3_V1.0_PrintOff/`.

### Network & Configuration

| Module | Purpose |
|---|---|
| `Lan_setting.py` | `resetDHCP()`, `configureStaticNetwork()`, `device_provisioning()` |
| `Configure_Network_7.py` | Low-level network interface configuration |
| `Lan_Info_Collector_2.py` | Reads current LAN interface state |
| `network_info.py` / `getNetworkInfo.py` | Returns IP, MAC, gateway information |

### Device & Provisioning

| Module | Purpose |
|---|---|
| `DeviceProvisioning_Module.py` | Provisions a device with default MQTT/network config |
| `device_parameters_module.py` | Read/write device parameters from `device_config.db` |
| `logical_params_module.py` | Read/write logical parameters |
| `externalDeviceConfig.py` | External device configuration helpers |
| `json_db_module.py` | JSON-based parameter storage |

### OTA Updates

| Module | Purpose |
|---|---|
| `ota2.py` | Core OTA update logic |
| `netota.py` | Network-aware OTA implementation |

### Data & Buffers

| Module | Purpose |
|---|---|
| `database_handler.py` | Higher-level database operations |
| `buffer_manager.py` | In-memory buffer/queue for telemetry data |
| `serial_data_logger.py` | Logs data arriving over serial port |
| `clear_all_data.py` | Wipes all stored data |

### RTC & Hardware Helpers

| Module | Purpose |
|---|---|
| `SDL_DS1307.py` | I²C Real-Time Clock read/write |
| `SerialCommunication.py` | Serial port open/read/write |
| `shiftRegister.py` | Shift-register GPIO control for outputs |
| `Adafruit_CharLCD.py` | Character LCD display driver |

### Helper Functions in `seple.py`

| Function | Description |
|---|---|
| `get_uptime()` | Returns system uptime in seconds from `/proc/uptime` |
| `get_cpu_freq()` | Returns CPU frequency |
| `get_ip_address()` | Returns the active IP address |
| `check_user_access(perms)` | Role-based access check |
| `initialize_users()` | Seeds default users on first run |
| `format_and_center(text, width)` | Pads text for 32-char LCD |
| `safe_read(path)` | File read with exception handling |
| `safe_write(path, content)` | File write with exception handling |
| `read_zone_file(path)` | Parses zone configuration file |
| `log_file_change(file_type)` | Records a config-change event to `systemLogs` |

---

## Hardware Integrations

### Camera / NVR Systems

| Module | Vendor | Protocol |
|---|---|---|
| `hikvision1_biometric_14.py` | Hikvision | ISAPI (HTTP/REST) |
| `hik_RTC_sync.py` | Hikvision | ISAPI |
| `Hik_SD_Card_REC_Cam_Info_Status_int.py` | Hikvision | ISAPI |
| `dahua_nvr_dvr_get_store_json_7i.py` | Dahua | CGI / HTTP |
| `dahua_RTC_sync.py` | Dahua | CGI |
| `Dahua_Recording_SD_Card_Cam_Info_Status_int.py` | Dahua | CGI |
| `Extract_Logs_Dahua_41.py` | Dahua | CGI |
| `nvr_dvr_bacs_integration_9.py` | Generic NVR/DVR | HTTP |

The web server stores NVR credentials (IP, username, password) in `sepleDB.db` and the service modules query the cameras directly over the local network.

### GPIO & Embedded Peripherals

| Module | Interface | Purpose |
|---|---|---|
| `SDL_DS1307.py` | I²C | Real-time clock |
| `SDL_Pi_TCA9545/` | I²C | I²C multiplexer (TCA9545) |
| `shiftRegister.py` | GPIO | Shift-register-based output control |
| `Adafruit_CharLCD.py` | GPIO | 16×2 / 20×4 character LCD |
| `SerialCommunication.py` | UART/Serial | Serial port for sub-systems |

---

## MQTT & IoT Connectivity

### ThingsBoard Integration

- **Library:** `paho-mqtt==1.6.1`
- **Module:** `thingsboard_mqtt_publisher.py`
- **Credentials** stored in `modem_config.db`

Default connection parameters (overridable via provisioning):

| Parameter | Default |
|---|---|
| Access Token | `6dNkl093nG4HvksMmYDD` |
| Client ID | `pt2gv4dhnol87qgt2lyw` |
| Username | `qdg6k3nm8quom2u5u4lv` |
| Password | `3thogxnhdanzkje0vuyw` |
| Device Name | `Dexter-HMS` |
| Transport | Ethernet (primary) |

### Web Endpoints for MQTT/Cloud Configuration

| Endpoint | Purpose |
|---|---|
| `POST /acces_token` | Set MQTT access-token credentials |
| `POST /x509` | Upload X.509 certificates for mTLS |
| `POST /mqtt_basic` | Set MQTT username/password credentials |

---

## Dependencies

Full list from `requirements.txt` (45+ packages):

### Core Web Framework

| Package | Version |
|---|---|
| Flask | 2.2.5 |
| Werkzeug | 2.2.3 |
| Jinja2 | 3.1.2 |
| itsdangerous | 2.1.2 |
| MarkupSafe | 2.1.1 |
| click | 8.1.3 |

### Flask Extensions

| Package | Version | Purpose |
|---|---|---|
| Flask-Cors | 3.1.1 | Cross-Origin Resource Sharing |
| Flask-Mail | 0.9.1 | Email sending |
| Flask-MySQL | 1.5.2 | MySQL connector |
| Flask-SQLAlchemy | 2.5.1 | ORM |
| Flask-WTF | 1.0.1 | WTForms / CSRF |
| flask-talisman | 1.1.0 | Security headers |

### Database & ORM

| Package | Version |
|---|---|
| SQLAlchemy | 1.4.46 |
| PyMySQL | 1.0.2 |
| mysqlclient | 2.1.1 |
| pymongo | 4.3.3 |
| greenlet | 2.0.2 |

### Security

| Package | Version |
|---|---|
| bcrypt | 3.1.7 |
| cryptography | 39.0.1 |
| PyNaCl | 1.5.0 |
| WTForms | 3.0.1 |

### IoT & Networking

| Package | Version |
|---|---|
| paho-mqtt | 1.6.1 |
| paramiko | 2.11.0 |
| requests | 2.31.0 |
| dnspython | 2.3.0 |

### System Utilities

| Package | Purpose |
|---|---|
| psutil | CPU, memory, disk, network monitoring |
| retrying | Retry decorator |
| gunicorn 20.1.0 | Production WSGI server |

### PDF Processing

| Package | Version |
|---|---|
| PyMuPDF | 1.22.3 |
| PyMuPDFb | 1.22.3 |

---

## Data Flow

### Configuration Update Flow

```
HTML Form (template)
  │
  │ form submit / JavaScript fetch
  ▼
Flask Route Handler (POST or PUT)
  │
  ├─ Session/auth check
  ├─ Parse request.form or request.json
  ├─ create_connection("sepleDB.db")
  ├─ SQL INSERT / UPDATE
  ├─ Optional: call service module (e.g. Lan_setting.configureStaticNetwork())
  └─ Return JSON {"status": "ok"} or redirect
  │
  ▼
Browser receives response
  └─ JavaScript shows success/error toast or reloads page
```

### Telemetry / Log Flow

```
Hardware event or periodic timer
  └─ Service module detects event
       └─ INSERT INTO systemLogs (dexterpanel2.db)
            └─ GET /logs → render_template("logs.html", logs=rows)
```

### MQTT Publish Flow

```
Device state change
  └─ thingsboard_mqtt_publisher.publish(payload)
       └─ paho-mqtt client → TCP → ThingsBoard server
```

---

## Request Lifecycle

```
1. HTTP request arrives on 0.0.0.0:5001
2. Flask WSGI layer routes to matching route decorator
3. @app.after_request runs after handler returns (adds cache headers)
4. Route handler:
   a. Check session["username"] → redirect /login if missing
   b. (Optional) check_user_access() for role-restricted pages
   c. Read request data (request.form / request.json / request.args)
   d. Open SQLite connection via create_connection()
   e. Execute query / call service module
   f. Close connection
   g. Return render_template() or jsonify() response
5. Response sent to client
```

---

## Deployment

### Development (current default)

```bash
/usr/bin/python3 /home/pi/Test3/webserver/seple.py
# Starts Flask debug server on 0.0.0.0:5001, threaded=True
```

### Production (recommended)

Use **gunicorn** (already in requirements.txt):

```bash
gunicorn -w 4 -b 0.0.0.0:5001 "seple:app"
```

### Startup on Boot (Raspberry Pi)

The `webserver_V3_integration.sh` script is intended to be called from a systemd service or `rc.local` to auto-start the server on boot.

Example systemd unit:

```ini
[Unit]
Description=Dexter HMS Web Server
After=network.target

[Service]
ExecStart=/bin/bash /home/pi/Test3/webserver/webserver_V3_integration.sh
Restart=on-failure
User=pi

[Install]
WantedBy=multi-user.target
```

### Network Access

The server binds to `0.0.0.0:5001`, meaning it is reachable on:

- `http://<device-LAN-IP>:5001` — from the local network
- `http://localhost:5001` — from the device itself
