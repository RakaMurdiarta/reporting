import os
import json

VIEW_STATES = "temp/views.json"


def read_view():
    try:
        if os.path.exists(VIEW_STATES):
            with open(VIEW_STATES, "r") as f:
                return json.load(f)
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {}


def write_view(views):
    with open(VIEW_STATES, "w") as f:
        json.dump(views, f)
