import os
import glob
import random
import string
from datetime import datetime


def _random_bytes(size: int) -> bytes:
    return os.urandom(size)


def _scramble_content(original: bytes) -> bytes:
    # Simple XOR scramble to simulate encryption without dependencies
    # XOR key (165 in decimal)
    key = 0xA5
    return bytes([b ^ key for b in original])


def _write_log(log_path: str, message: str) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.utcnow().isoformat()}Z | {message}\n")


def simulate_attack(live_dir: str, log_path: str) -> dict:
    """Simulate a ransomware attack by scrambling files in live_dir.
    - Renames files to add .ENCRYPTED extension
    - Replaces content with scrambled bytes
    - Drops a ransom note
    - Writes to detection log
    Returns a summary dict
    """

    os.makedirs(live_dir, exist_ok=True)

    target_files = [
        f for f in glob.glob(os.path.join(live_dir, "**"), recursive=True)
        if os.path.isfile(f) and not f.endswith(".ENCRYPTED") and os.path.basename(f) != "READ_ME_RESTORE.txt"
    ]

    affected = []
    for path in target_files:
        try:
            with open(path, "rb") as rf:
                data = rf.read()
            scrambled = _scramble_content(data if data else _random_bytes(512))
            enc_path = path + ".ENCRYPTED"
            with open(enc_path, "wb") as wf:
                wf.write(scrambled)
            os.remove(path)
            affected.append(os.path.basename(enc_path))
        except Exception as e:
            _write_log(log_path, f"ERROR scrambling {path}: {e}")

    # Drop ransom note
    note_path = os.path.join(live_dir, "READ_ME_RESTORE.txt")
    note = (
        "Your files have been encrypted.\n"
        "This is a simulation for demo purposes.\n"
        "Use the Restore button in the dashboard to recover from backup.\n"
    )
    with open(note_path, "w", encoding="utf-8") as nf:
        nf.write(note)

    _write_log(log_path, f"ATTACK simulated against {live_dir} | files={len(affected)}")

    return {"affected_count": len(affected), "note": note_path}

