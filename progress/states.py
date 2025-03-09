import os
import json
PROGRESS_FILE = 'temp/progress.json'
PROCCESSING_FILE = 'temp/proccessing.json'

def read_progress():
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {} 

def write_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def read_proccessing():
    try:
        if os.path.exists(PROCCESSING_FILE):
            with open(PROCCESSING_FILE, 'r') as f:
                return json.load(f)
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {} 
def write_proccessing(progress):
    with open(PROCCESSING_FILE, 'w') as f:
        json.dump(progress, f)