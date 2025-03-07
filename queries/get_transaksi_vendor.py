from dbutils.pooled_db import PooledDB
import csv
from tqdm import tqdm
import pymysql
from pool import db_pool
from progress import backgorund

def get_transaksi_vendor(entitas, coa, start_date, end_date, task_id):
    sql = f"""
    SELECT
        gl_transaksi.company_vendor_id,
        gl_transaksi_detail.coa,
        gl_transaksi_detail.debit,
        gl_transaksi_detail.kredit,
        gl_transaksi.no_gl_transaksi,
        gl_transaksi.keterangan,
        gl_transaksi.tanggal_transaksi,
        LEFT(gl_transaksi_detail.coa,1) as coa_prefix
    FROM gl_transaksi
    JOIN gl_transaksi_detail
        ON gl_transaksi_detail.transaksi_id = gl_transaksi.id
    WHERE gl_transaksi.tanggal_transaksi BETWEEN %s AND %s
        AND gl_transaksi.status_lvl_1 = 1
        AND gl_transaksi_detail.coa = %s
        AND gl_transaksi.company_CompanyID LIKE %s
    """
    csv_file_path = 'transaksi.csv'

    try:
        progress = backgorund.read_progress()
        progress[task_id] = {"status": "started"}

        conn = db_pool.pool.connection()
        cursor = conn.cursor()
        chunk_size = 6000
        cursor.execute(sql, (start_date, end_date, coa, f"{entitas}%"))
        columns = [desc[0] for desc in cursor.description]
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(columns)

            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break  # Exit the loop when no more data is available
                writer.writerows(rows)
        cursor.close()
        conn.close()
        progress[task_id]["status"] = "completed"
        print(f"Data exported to {csv_file_path}")
    except pymysql.MySQLError as e:
        print(f"Error executing query: {e}")
        progress[task_id]["status"] = "failed"
        return None    
    finally:
        backgorund.write_progress(progress)
        if conn:
            conn.close()
            db_pool.pool.close()