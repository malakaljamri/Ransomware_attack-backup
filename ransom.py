from flask import Flask, request, jsonify, render_template, redirect, url_for, send_from_directory, Response
import os
import threading
import time

# Optional serial
try:
    import serial  # pyserial
except Exception:
    serial = None

import importlib.util
from jinja2 import Environment, FileSystemLoader

app = Flask(__name__)

# Config: directories
BASE = os.path.abspath(os.path.dirname(__file__))

# Veeam dashboard paths
VEEAM_ROOT = os.path.join(BASE, "Veeam-Backup-Dash")
VEEAM_TEMPLATES = os.path.join(VEEAM_ROOT, "templates")
VEEAM_STATIC = os.path.join(VEEAM_ROOT, "static")

# Prefer the Veeam dashboard's ransomware_simulation if present, else fallback to top-level
SIM_ROOT_VEEAM = os.path.join(VEEAM_ROOT, "ransomware_simulation")
SIM_ROOT_TOP = os.path.join(BASE, "ransomware_simulation")
SIM_ROOT = SIM_ROOT_VEEAM if os.path.isdir(SIM_ROOT_VEEAM) else SIM_ROOT_TOP

LIVE_DIR = os.path.join(SIM_ROOT, "live_folder")
BACKUP_DIR = os.path.join(SIM_ROOT, "backup_repository")
LOG_DIR = os.path.join(SIM_ROOT, "logs")
LOG_PATH = os.path.join(LOG_DIR, "simulation.log")

# Dynamic import helpers to load modules from SIM_ROOT
def _load_function(module_path: str, func_name: str):
    spec = importlib.util.spec_from_file_location(
        f"_dyn_{os.path.basename(module_path)}", module_path
    )
    if spec and spec.loader:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        return getattr(mod, func_name)
    raise ImportError(f"Could not load {func_name} from {module_path}")

_simulate_attack = _load_function(os.path.join(SIM_ROOT, "simulate_attack.py"), "simulate_attack")
_restore_from_backup = _load_function(os.path.join(SIM_ROOT, "restore_script.py"), "restore_from_backup")

# Arduino config from env
ARDUINO_PORT = os.environ.get("ARDUINO_PORT")
ARDUINO_BAUD = int(os.environ.get("ARDUINO_BAUD", "9600"))
ARDUINO_START_CMD = os.environ.get("ARDUINO_START_CMD", "START")

_serial_lock = threading.Lock()
_serial_obj = None
_last_arduino_cmd = None

# --- Simple countdown timer to support templates/ransom.html ---
timer_total = int(os.environ.get("RANSOM_TIMER_SECONDS", str(60*60)))  # default 1 hour
timer = timer_total
attack_active = False
_timer_thread_started = False

def _log(msg: str) -> None:
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} | {msg}\n")

def _detect_sim_status() -> str:
    try:
        # Compromised if ransom note or any .ENCRYPTED exists
        if os.path.exists(os.path.join(LIVE_DIR, "READ_ME_RESTORE.txt")):
            return "compromised"
        for root, _, files in os.walk(LIVE_DIR):
            if any(f.endswith('.ENCRYPTED') for f in files):
                return "compromised"
        return "safe"
    except Exception:
        return "unknown"

def _get_serial():
    global _serial_obj
    if serial is None or not ARDUINO_PORT:
        return None
    with _serial_lock:
        if _serial_obj is not None:
            return _serial_obj
        try:
            _serial_obj = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=2)
            time.sleep(2.0)  # let Arduino reset
            _log(f"SERIAL connected {ARDUINO_PORT}@{ARDUINO_BAUD}")
        except Exception as e:
            _log(f"SERIAL connect error: {e}")
            _serial_obj = None
        return _serial_obj

def _arduino_send(cmd: str) -> bool:
    global _last_arduino_cmd
    ser = _get_serial()
    if ser is None:
        _log(f"SERIAL unavailable, skipped cmd '{cmd}'")
        return False
    try:
        ser.write((cmd.strip() + "\n").encode("utf-8"))
        ser.flush()
        _last_arduino_cmd = cmd.strip().upper()
        _log(f"SERIAL sent '{_last_arduino_cmd}'")
        return True
    except Exception as e:
        _log(f"SERIAL write error '{cmd}': {e}")
        return False

def _arduino_startup_kick():
    try:
        # small delay to allow server to come up and serial to settle
        time.sleep(1.5)
        _arduino_send(ARDUINO_START_CMD)
    except Exception:
        pass

def _timer_loop():
    global timer
    while True:
        time.sleep(1)
        if attack_active and timer > 0:
            timer -= 1

@app.route("/", methods=["GET"]) 
def root():
    return redirect(url_for("register"))

# --- UI Flow: Register -> Malware Info (instead of SCADA) ---
@app.route("/register", methods=["GET"])
def register():
    return render_template("register.html")

@app.route("/submit_register", methods=["POST"])
def submit_register():
    # In this streamlined demo, we skip DB/session and go directly to the ransomware page
    return redirect(url_for("ransom"))

@app.route("/ransom", methods=["GET", "POST"]) 
def ransom():
    # Trigger the simulated attack so admin sees the encrypted state instead of SCADA
    _simulate_attack(LIVE_DIR, LOG_PATH)
    # Stop/lock the pump during the attack
    _arduino_send("STOP")
    # Start/Reset timer when ransom page is shown
    global attack_active, timer
    attack_active = True
    timer = timer_total
    return render_template("ransom.html")

@app.route("/status", methods=["GET"]) 
def status():
    live_count = 0
    backup_count = 0
    if os.path.isdir(LIVE_DIR):
        for _, _, files in os.walk(LIVE_DIR):
            live_count += len(files)
    if os.path.isdir(BACKUP_DIR):
        for _, _, files in os.walk(BACKUP_DIR):
            backup_count += len(files)
    return jsonify({
        "live_dir": LIVE_DIR,
        "backup_dir": BACKUP_DIR,
        "log_path": LOG_PATH,
        "live_files": live_count,
        "backup_files": backup_count,
        "serial_available": serial is not None,
        "arduino_port": ARDUINO_PORT or "",
        "arduino_last_cmd": _last_arduino_cmd,
    })

# --- Veeam dashboard exposure ---
@app.route("/veeam", methods=["GET"]) 
def veeam_index():
    # Render Veeam dashboard with context (Jinja2 environment pointing to VEEAM_TEMPLATES)
    env = Environment(loader=FileSystemLoader(VEEAM_TEMPLATES))
    tpl = env.get_template("index.html")
    sim_status = {"status": _detect_sim_status()}
    # Minimal demo metrics/data for template
    metrics = {"success_rate": 97, "total_jobs": 12, "storage_used_percent": 63}
    data = {
        "jobs": [
            {"Name": "Daily Backup", "LastResult": "Success", "LastRun": "2025-11-26T22:00Z"},
            {"Name": "Weekly Full", "LastResult": "Success", "LastRun": "2025-11-24T02:00Z"},
            {"Name": "DB Snapshots", "LastResult": "Warning", "LastRun": "2025-11-26T23:30Z"},
        ],
        "sessions": [
            {"Name": "Daily Backup", "State": "Stopped", "Result": "Success", "CreationTime": "2025-11-26T22:00Z"},
            {"Name": "Weekly Full", "State": "Stopped", "Result": "Success", "CreationTime": "2025-11-24T02:00Z"},
            {"Name": "DB Snapshots", "State": "Stopped", "Result": "Warning", "CreationTime": "2025-11-26T23:30Z"},
        ],
    }
    html = tpl.render(sim_status=sim_status, metrics=metrics, data=data)
    return Response(html, mimetype="text/html")

@app.route('/veeam/static/<path:filename>')
def veeam_static(filename):
    # Serve Veeam dashboard static assets
    return send_from_directory(VEEAM_STATIC, filename)

@app.route("/get_timer", methods=["GET"]) 
def get_timer():
    return jsonify({"timer": timer})

# --- Veeam API for dashboard JS ---
@app.route('/api/ransomware/status', methods=['GET'])
def api_status():
    return jsonify({"status": _detect_sim_status()})

@app.route('/api/ransomware/simulate', methods=['POST'])
def api_simulate():
    result = _simulate_attack(LIVE_DIR, LOG_PATH)
    _arduino_send("STOP")
    status = {"status": _detect_sim_status()}
    return jsonify({"result": result, "status": status})

@app.route('/api/ransomware/restore', methods=['POST'])
def api_restore():
    result = _restore_from_backup(BACKUP_DIR, LIVE_DIR, LOG_PATH)
    _arduino_send("START")
    global attack_active, timer
    attack_active = False
    timer = 0
    status = {"status": _detect_sim_status()}
    return jsonify({"result": result, "status": status})

@app.route('/api/data', methods=['GET'])
def api_data():
    # Minimal placeholder for dashboard auto-refresh
    return jsonify({"ok": True, "ts": time.time()})

@app.route("/simulate", methods=["POST"]) 
def simulate():
    summary = _simulate_attack(LIVE_DIR, LOG_PATH)
    # Optional: stop the pump during attack
    _arduino_send("STOP")
    return jsonify({"ok": True, "action": "simulate", "summary": summary})

@app.route("/restore", methods=["POST"]) 
def restore():
    summary = _restore_from_backup(BACKUP_DIR, LIVE_DIR, LOG_PATH)
    # Optional: restart the pump after restore
    _arduino_send("START")
    # Stop the countdown on restore
    global attack_active, timer
    attack_active = False
    timer = 0
    return jsonify({"ok": True, "action": "restore", "summary": summary})

# Challenge-gated shutdown: mirrors previous behavior but now performs a restore
@app.route('/shutdown', methods=['POST']) 
def shutdown():
    password = request.form.get('password')
    username = request.headers.get('username')
    final = 'supersecretkey'  # keep compatibility with old challenge

    if password == final and bool(username):
        # Perform restore from backup as the "shutdown" action
        summary = _restore_from_backup(BACKUP_DIR, LIVE_DIR, LOG_PATH)
        # Resume normal operation on Arduino
        _arduino_send("START")
        # Stop the countdown
        global attack_active, timer
        attack_active = False
        timer = 0
        return jsonify({"message": "Successful Shutdown with restore", "summary": summary}), 202
    else:
        return jsonify({"error": "Wrong Password"}), 401

@app.route("/arduino/start", methods=["POST"]) 
def arduino_start():
    sent = _arduino_send("START")
    return jsonify({"ok": sent})

@app.route("/arduino/stop", methods=["POST"]) 
def arduino_stop():
    sent = _arduino_send("STOP")
    return jsonify({"ok": sent})

if __name__ == "__main__":
    # Kick the pump into motion at startup (fast/normal depends on ARDUINO_START_CMD)
    threading.Thread(target=_arduino_startup_kick, daemon=True).start()
    # Start countdown timer loop
    if not _timer_thread_started:
        threading.Thread(target=_timer_loop, daemon=True).start()
        _timer_thread_started = True
    app.run(host="0.0.0.0", port=5001, debug=True)
