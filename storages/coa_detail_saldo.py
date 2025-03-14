import os
import json

COA_DETAIL_PATH = "temp/coa_detail_saldo.json"


def read_coa_detail_saldo():
    try:
        if os.path.exists(COA_DETAIL_PATH):
            with open(COA_DETAIL_PATH, "r") as f:
                return json.load(f)
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {}


def write_coa_detail_saldo(progress):
    with open(COA_DETAIL_PATH, "w") as f:
        json.dump(progress, f)
