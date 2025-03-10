import pymysql
from pool import db_pool
from progress import states
import csv
from utils import init_state_progress,writer_csv_helper

def get_transaksi_tanpa_vendor(task_id, coa, entitas, start_date, end_date):
    sql= f"""
    SELECT *
    FROM gl_transaksi
    JOIN gl_transaksi_detail
        ON gl_transaksi_detail.transaksi_id = gl_transaksi.id
    WHERE gl_transaksi.tanggal_transaksi BETWEEN %s AND %s
        AND gl_transaksi_detail.deleted_at IS NULL
        AND gl_transaksi.company_CompanyID LIKE %s
        AND gl_transaksi.company_vendor_id IS NULL
        AND gl_transaksi_detail.coa = %s
        AND gl_transaksi.status_lvl_1 = 1
    ORDER BY gl_transaksi.tanggal_transaksi DESC
    """

    csv_file_path = f'temp/{task_id}_transaksi_tanpa_vendor.csv'
    try:
        conn = db_pool.pool.connection()
        cursor = conn.cursor()
        chunk_size = 6000
        cursor.execute(sql, (start_date, end_date, f"{entitas}%",coa))
        columns = [desc[0] for desc in cursor.description]

        def writer_csv():
            writer_csv_helper.writer_csv_helper(chunk_size,csv_file_path,columns,cursor)
        
        init_state_progress.init_state_progress(task_id=task_id,task_name='get_transaksi_tanpa_vendor',csv_file_path=csv_file_path,callback=writer_csv)

    except pymysql.MySQLError as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        if conn:
            conn.close()
            db_pool.pool.close()


def get_saldo_awal_transaksi_tanpa_vendor():
    sql="""
    SELECT
    FROM
    WHERE
    """