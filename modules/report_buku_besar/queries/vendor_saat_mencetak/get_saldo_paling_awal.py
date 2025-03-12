from pool import db_pool
import csv
import pymysql
from progress import states
from modules.report_buku_besar.queries.vendor_saat_mencetak.constant.index import (
    constants,
)


def get_saldo_paling_awal(task_id: str, coa_number: str, entitas: str):
    level = len(coa_number)
    coaLevels = {
        "10": "coa_level_5",
        "7": "coa_level_4",
        "5": "coa_level_3",
        "3": "coa_level_2",
        "default": "coa_level_1",
    }
    table = coaLevels.get(str(level), coaLevels["default"])
    sql = f"""
    SELECT
        SUM(saldo_paling_awal) AS saldo_paling_awal
    FROM {table}
    WHERE id = %s AND company_CompanyID LIKE %s AND deleted_at IS NULL
    """

    csv_file_path = f"temp/{task_id}_{constants.get_saldo_paling_awal}.csv"
    try:
        progress = states.read_progress()
        if task_id not in progress:
            progress[task_id] = {
                "status": "started",
                "filenames": {},
                "tasks": {},
                "range_date": {},
            }
        progress[task_id]["tasks"][constants.get_saldo_paling_awal] = "in_progress"
        conn = db_pool.pool.connection()
        cursor = conn.cursor()
        chunk_size = 6000
        cursor.execute(sql, (coa_number, f"{entitas}%"))
        columns = [desc[0] for desc in cursor.description]
        with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(columns)

            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break  # Exit the loop when no more data is available
                writer.writerows(rows)
        cursor.close()
        conn.close()
        progress[task_id]["tasks"][constants.get_saldo_paling_awal] = "completed"
        progress[task_id]["filenames"][constants.get_saldo_paling_awal] = csv_file_path
        if all(status == "completed" for status in progress[task_id]["tasks"].values()):
            progress[task_id]["status"] = "completed"
        print(f"Data exported to {csv_file_path}")
        states.write_progress(progress)
    except pymysql.MySQLError as e:
        print(f"Error executing query: {e}")
        progress[task_id]["tasks"][constants.get_saldo_paling_awal] = "failed"
        progress[task_id]["status"] = "failed"
        states.write_progress(progress)

        return None
    finally:
        if conn:
            conn.close()
            db_pool.pool.close()
