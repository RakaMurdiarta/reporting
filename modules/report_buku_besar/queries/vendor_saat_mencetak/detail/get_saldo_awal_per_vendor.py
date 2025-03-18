import pymysql
from pool import db_pool
from progress import states
import csv
from utils import preparation_helper, writer_csv_helper
from modules.report_buku_besar.queries.vendor_saat_mencetak.constant.index import (
    constants,
)


def get_saldo_awal_per_vendor(task_id, coa, entitas, start_date, end_date):

    if str(coa)[0] in ["1", "5", "6", "7", "8"]:
        saldo_column = "SUM(debit - kredit) AS Saldo"
    else:
        saldo_column = "SUM(kredit - debit) AS Saldo"

    sql = f"""
    SELECT
        gl_transaksi.company_vendor_id,
        {saldo_column}
    FROM gl_transaksi
    JOIN gl_transaksi_detail
        ON gl_transaksi_detail.transaksi_id = gl_transaksi.id
    WHERE gl_transaksi.company_CompanyID LIKE %s
        AND gl_transaksi.status_lvl_1 = 1
        AND gl_transaksi_detail.coa = %s
        AND gl_transaksi_detail.deleted_at IS NULL
        AND gl_transaksi.tanggal_transaksi < %s
    GROUP BY gl_transaksi.company_vendor_id
    """

    csv_file_path = f"temp/{task_id}_{constants.get_saldo_awal_per_vendor}.csv"
    try:
        conn = db_pool.pool.connection()
        cursor = conn.cursor()
        chunk_size = 6000

        def sql_exec():
            cursor.execute(sql, (f"{entitas}%", coa, start_date))

        def writer_csv():
            writer_csv_helper.writer_csv_helper(chunk_size, csv_file_path, cursor)

        preparation_helper.preparation_helper(
            task_id=task_id,
            task_name=constants.get_saldo_awal_per_vendor,
            csv_file_path=csv_file_path,
            writer_csv_exec=writer_csv,
            sql_exec=sql_exec,
            start_date=start_date,
            end_date=end_date,
        )

    except pymysql.MySQLError as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        if conn:
            conn.close()
            db_pool.pool.close()
