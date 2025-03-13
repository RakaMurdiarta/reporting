from pool import db_pool
import csv
import pymysql
from progress import states
from modules.report_buku_besar.queries.proyek_pada_vendor.constant.index import (
    constants,
)
from utils import preparation_helper, writer_csv_helper


def get_proyek_by_vendor(
    task_id: str, coa_number: str, entitas: str, start_date: str, end_date: str
):
    sql = f"""
    SELECT
        gl_transaksi.company_vendor_id,
        company.Name as Vendor
    FROM gl_transaksi
    INNER JOIN gl_transaksi_detail
        ON gl_transaksi.id = gl_transaksi_detail.transaksi_id
    INNER JOIN company
	    ON gl_transaksi.company_vendor_id = company.CompanyID
    WHERE gl_transaksi.company_CompanyID like %s
        AND gl_transaksi.status_lvl_1 = 1
        AND gl_transaksi_detail.deleted_at IS NULL
        AND gl_transaksi_detail.coa = %s
    GROUP BY gl_transaksi.company_vendor_id
    """

    csv_file_path = (
        f"temp/{task_id}_{constants.get_company_vendors_proyek_pada_vendor}.csv"
    )
    try:
        conn = db_pool.pool.connection()
        cursor = conn.cursor()
        chunk_size = 6000

        def sql_exec():
            cursor.execute(sql, (f"{entitas}%", coa_number))

        def writer_csv():
            writer_csv_helper.writer_csv_helper(chunk_size, csv_file_path, cursor)

        preparation_helper.preparation_helper(
            task_id=task_id,
            task_name=constants.get_company_vendors_proyek_pada_vendor,
            csv_file_path=csv_file_path,
            writer_csv_exec=writer_csv,
            sql_exec=sql_exec,
            end_date=end_date,
            start_date=start_date,
        )
    except pymysql.MySQLError as e:
        print(f"Error executing query: {e}")
        raise e
    finally:
        if conn:
            conn.close()
            db_pool.pool.close()
