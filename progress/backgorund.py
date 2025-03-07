import os
import json
PROGRESS_FILE = 'progress.json'

def read_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def write_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)