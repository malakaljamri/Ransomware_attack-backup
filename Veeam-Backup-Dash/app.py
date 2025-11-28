from flask import Flask, render_template, jsonify, request
import json
from datetime import datetime
from collections import defaultdict
import os
import shutil
import glob

# Ransomware simulation modules
from ransomware_simulation.simulate_attack import simulate_attack
from ransomware_simulation.restore_script import restore_from_backup

app = Flask(__name__)


# -----------------------------
# Converters
# -----------------------------

def convert_state(state_code):
    states = {
        -1: "Stopped",
        0: "Starting",
        1: "Working",
        2: "Idle"
    }
    return states.get(state_code, f"Unknown ({state_code})")

def convert_result(result_code):
    results = {
        0: "Success",
        1: "Warning",
        2: "Failed"
    }
    return results.get(result_code, f"Unknown ({result_code})")

def convert_date(date_string):
    if not date_string or not date_string.startswith('/Date('):
        return date_string
    try:
        timestamp = int(date_string[6:-2])
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return date_string


# -----------------------------
# LOAD DATA
# -----------------------------

def load_json(path):
    try:
        with open(path, "r", encoding="utf-16") as f:
            return json.load(f)
    except:
        return []


def load_veeam_data():

    sessions_raw = load_json("data/backup_sessions.json")
    jobs_raw = load_json("data/backup_jobs.json")
    storage_raw = load_json("data/storage_info.json")

    # Convert sessions
    sessions = []
    for s in sessions_raw:
        sessions.append({
            "Name": s.get("Name", "Unknown"),
            "State": convert_state(s.get("State")),
            "Result": convert_result(s.get("Result")),
            "CreationTime": convert_date(s.get("CreationTime")),
            "EndTime": convert_date(s.get("EndTime"))
        })

    # -----------------------------
    # FIX 1 — Group sessions per job & pick latest
    # -----------------------------
    grouped = defaultdict(list)

    for s in sessions_raw:
        job_name = s.get("Name", "").split("(")[0].strip()
        grouped[job_name].append(s)

    latest_sessions_per_job = {}

    for job, sess_list in grouped.items():
        sess_list.sort(key=lambda x: x.get("CreationTime", ""), reverse=True)
        latest_sessions_per_job[job] = sess_list[0]  # only latest

    # Build job list
    jobs = []
    for j in jobs_raw:
        name = j.get("Name", "Unknown")
        latest = latest_sessions_per_job.get(name)

        if latest:
            jobs.append({
                "Name": name,
                "LastState": convert_state(latest.get("State")),
                "LastResult": convert_result(latest.get("Result")),
                "LastRun": convert_date(latest.get("CreationTime"))
            })
        else:
            jobs.append({
                "Name": name,
                "LastState": "Never Run",
                "LastResult": "Never Run",
                "LastRun": "Never"
            })

    # -----------------------------
    # FIX 2 — Keep only latest 10 sessions
    # -----------------------------
    sessions_sorted = sorted(
        sessions,
        key=lambda x: x["CreationTime"],
        reverse=True
    )
    sessions_top10 = sessions_sorted[:13]

    # -----------------------------
    # FIX 3 — Use accurate storage percent
    # -----------------------------
    storage = []
    for repo in storage_raw:
        free = repo.get("FreeSpaceGB", 0)
        total = repo.get("TotalSpaceGB", 0)
        used = total - free

        percent_used = (used / total * 100) if total > 0 else 0

        storage.append({
            "Name": repo.get("Name", "Unknown Repository"),
            "FreeSpaceGB": free,
            "TotalSpaceGB": total,
            "UsedPercent": round(percent_used, 1)
        })

    return {
        "sessions": sessions_top10,
        "jobs": jobs,
        "storage": storage
    }


# -----------------------------
# RANSOMWARE SIMULATION HELPERS
# -----------------------------

BASE_SIM_DIR = os.path.join(os.path.dirname(__file__), "ransomware_simulation")
LIVE_DIR = os.path.join(BASE_SIM_DIR, "live_folder")
BACKUP_DIR = os.path.join(BASE_SIM_DIR, "backup_repository")
LOG_PATH = os.path.join(BASE_SIM_DIR, "logs", "detection.log")


def seed_environment():
    os.makedirs(LIVE_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    # If backup empty, create sample files
    if not any(os.scandir(BACKUP_DIR)):
        sample_files = {
            "finance_q4.csv": "date,amount\n2025-11-01,12000\n2025-11-15,-2300\n",
            "readme.txt": "Sample business documents for ransomware simulation.\n",
            "reports/summary.md": "# Quarterly Summary\nAll systems operational.\n",
        }
        for rel, content in sample_files.items():
            target = os.path.join(BACKUP_DIR, rel)
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
    # If live empty, copy from backup as initial state
    if not any(os.scandir(LIVE_DIR)):
        for root, dirs, files in os.walk(BACKUP_DIR):
            rel = os.path.relpath(root, BACKUP_DIR)
            target_root = os.path.join(LIVE_DIR, rel) if rel != "." else LIVE_DIR
            os.makedirs(target_root, exist_ok=True)
            for d in dirs:
                os.makedirs(os.path.join(target_root, d), exist_ok=True)
            for f in files:
                shutil.copy2(os.path.join(root, f), os.path.join(target_root, f))


def get_attack_status():
    # Detect presence of encrypted files or ransom note in live folder
    has_encrypted = any(
        f.endswith(".ENCRYPTED") for f in glob.glob(os.path.join(LIVE_DIR, "**", "*"), recursive=True) if os.path.isfile(f)
    )
    has_note = os.path.exists(os.path.join(LIVE_DIR, "READ_ME_RESTORE.txt"))
    status = "compromised" if (has_encrypted or has_note) else "healthy"
    return {"status": status, "has_encrypted": has_encrypted, "has_note": has_note}


# -----------------------------
# Metrics
# -----------------------------

def calculate_security_score(data):

    jobs = data["jobs"]
    storage = data["storage"]
    sessions = data["sessions"]

    score = 0

    # +20 encryption
    if any("encrypt" in j["Name"].lower() for j in jobs):
        score += 20

    # +20 immutable
    if any("immutable" in repo["Name"].lower() for repo in storage):
        score += 20

    # +20 offsite
    if any("cloud" in repo["Name"].lower() for repo in storage):
        score += 20

    # +20 offline
    if any("offline" in repo["Name"].lower() for repo in storage):
        score += 20

    # +20 last job success
    if sessions and sessions[0]["Result"] == "Success":
        score += 20

    return score


def calculate_metrics(data):

    sessions = data["sessions"]
    success_count = sum(1 for s in sessions if s["Result"] == "Success")
    total_sessions = len(sessions)

    storage = data["storage"]
    total_free = sum(s["FreeSpaceGB"] for s in storage)
    total_capacity = sum(s["TotalSpaceGB"] for s in storage)

    total_used = total_capacity - total_free
    storage_percent = (total_used / total_capacity * 100) if total_capacity else 0

    return {
        "success_rate": round(success_count / total_sessions * 100, 1) if total_sessions else 0,
        "storage_used_percent": round(storage_percent, 1),
        "security_score": calculate_security_score(data),
        "total_sessions": total_sessions,
        "total_jobs": len(data["jobs"])
    }


# -----------------------------
# ROUTES
# -----------------------------

@app.route("/")
def dashboard():
    veeam_data = load_veeam_data()
    metrics = calculate_metrics(veeam_data)
    # Ensure simulation environment exists
    seed_environment()
    sim_status = get_attack_status()
    return render_template("index.html", data=veeam_data, metrics=metrics, sim_status=sim_status)


@app.route("/api/data")
def api_data():
    veeam_data = load_veeam_data()
    metrics = calculate_metrics(veeam_data)
    return jsonify({"data": veeam_data, "metrics": metrics})


@app.route("/api/ransomware/status")
def api_ransomware_status():
    seed_environment()
    return jsonify(get_attack_status())


@app.route("/api/ransomware/simulate", methods=["POST"]) 
def api_ransomware_simulate():
    seed_environment()
    result = simulate_attack(LIVE_DIR, LOG_PATH)
    status = get_attack_status()
    return jsonify({"result": result, "status": status})


@app.route("/api/ransomware/restore", methods=["POST"]) 
def api_ransomware_restore():
    seed_environment()
    result = restore_from_backup(BACKUP_DIR, LIVE_DIR, LOG_PATH)
    status = get_attack_status()
    return jsonify({"result": result, "status": status})


@app.route("/debug")
def debug():
    d = load_veeam_data()
    return jsonify({
        "sessions": len(d["sessions"]),
        "jobs": len(d["jobs"]),
        "storage": len(d["storage"]),
        "sample_sessions": d["sessions"][:2]
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
