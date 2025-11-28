import os
import shutil
import glob
from datetime import datetime


# --- Helper: Write a log message with timestamp ---
def _write_log(log_path: str, message: str) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)  # Ensure log folder exists
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{datetime.utcnow().isoformat()}Z | {message}\n")  # Append log line


# --- Helper: Remove everything inside the live folder ---
def _clean_live_folder(live_dir: str) -> None:
    # Loop through all items in the folder
    for entry in os.listdir(live_dir):
        full = os.path.join(live_dir, entry)
        try:
            if os.path.isfile(full) or os.path.islink(full):
                os.remove(full)  # Delete files or symlinks
            else:
                shutil.rmtree(full)  # Delete folders recursively
        except Exception:
            # Ignore errors, best-effort cleanup
            pass


# --- Main function: Restore backup to live folder ---
def restore_from_backup(backup_dir: str, live_dir: str, log_path: str) -> dict:
    # Ensure backup and live folders exist
    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(live_dir, exist_ok=True)

    # --- Step 1: Remove any ransom/attack artifacts ---
    # Delete all encrypted files
    for enc in glob.glob(os.path.join(live_dir, "**", "*.ENCRYPTED"), recursive=True):
        try:
            os.remove(enc)
        except Exception:
            pass
    # Delete ransom note if exists
    note = os.path.join(live_dir, "READ_ME_RESTORE.txt")
    if os.path.exists(note):
        try:
            os.remove(note)
        except Exception:
            pass

    # --- Step 2: Clear live folder completely ---
    _clean_live_folder(live_dir)

    # --- Step 3: Copy backup files into live folder ---
    restored_files = 0
    for root, dirs, files in os.walk(backup_dir):
        rel = os.path.relpath(root, backup_dir)  # Relative path from backup folder
        target_root = os.path.join(live_dir, rel) if rel != "." else live_dir
        os.makedirs(target_root, exist_ok=True)  # Ensure folder exists
        # Create subfolders
        for d in dirs:
            os.makedirs(os.path.join(target_root, d), exist_ok=True)
        # Copy all files
        for f in files:
            src = os.path.join(root, f)
            dst = os.path.join(target_root, f)
            shutil.copy2(src, dst)  # Copy file with metadata
            restored_files += 1

    # --- Step 4: Log the restore action ---
    _write_log(log_path, f"RESTORE executed from {backup_dir} to {live_dir} | files={restored_files}")

    # Return summary
    return {"restored_count": restored_files}
