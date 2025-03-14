import pymysql
from storages import coa_detail_saldo as storage_coa
from pool import db_pool


def get_coa_detail_saldo(task_id: str, coa_number: str, entitas: str):

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

    sql_coa_label = f"""
    SELECT
        nama_coa
    FROM {table}
    WHERE id = %s AND company_CompanyID LIKE %s AND deleted_at IS NULL
    """

    try:
        store = storage_coa.read_coa_detail_saldo()
        conn = db_pool.pool.connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute(sql, (coa_number, f"{entitas}%"))
        result = cursor.fetchall()

        if task_id not in store:
            store[task_id] = {}

        for row in result:
            store[task_id]["saldo_paling_awal"] = row["saldo_paling_awal"] or 0

        cursor.execute(sql_coa_label, (coa_number, f"{entitas}%"))
        coa_label_result = cursor.fetchall()
        for row in coa_label_result:
            store[task_id]["coa_label"] = row["nama_coa"]

        storage_coa.write_coa_detail_saldo(store)
        cursor.close()
        conn.close()

        print(f"Data exported to json")
    except pymysql.MySQLError as e:
        print(f"Error executing query: {e}")
    finally:
        if conn:
            conn.close()
            db_pool.pool.close()
