import pymysql
from pool import db_pool
from progress import states
import csv
from utils import preparation_helper, writer_csv_helper


def get_transaksi_tanpa_vendor_rekap(task_id, coa, entitas, end_date):
    sql = f"""
    SELECT
        SUM(gl_transaksi_detail.debit) as debit,
        SUM(gl_transaksi_detail.kredit) as kredit
    FROM gl_transaksi
    INNER JOIN gl_transaksi_detail
        ON gl_transaksi.id = gl_transaksi_detail.transaksi_id
    WHERE gl_transaksi.company_CompanyID like %s
        AND gl_transaksi.company_vendor_id IS NULL
        AND gl_transaksi_detail.coa = %s
        AND gl_transaksi.status_lvl_1 = 1
        AND gl_transaksi.tanggal_transaksi <= %s
    """

    csv_file_path = f"temp/{task_id}_transaksi_tanpa_vendor_rekap.csv"
    try:
        conn = db_pool.pool.connection()
        cursor = conn.cursor()
        chunk_size = 6000

        def sql_exec():
            cursor.execute(sql, (f"{entitas}%", coa, end_date))

        def writer_csv():
            writer_csv_helper.writer_csv_helper(chunk_size, csv_file_path, cursor)

        preparation_helper.preparation_helper(
            task_id=task_id,
            task_name="get_transaksi_tanpa_vendor_rekap",
            csv_file_path=csv_file_path,
            writer_csv_exec=writer_csv,
            sql_exec=sql_exec,
        )

    except pymysql.MySQLError as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        if conn:
            conn.close()
            db_pool.pool.close()
