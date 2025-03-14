from pool import db_pool
import csv
import pymysql
from progress import states
import pandas as pd
from modules.report_buku_besar.queries.proyek_saat_mencetak.constant.index import (
    constants,
)
from utils import preparation_helper, writer_csv_helper


def get_transaksi_detail_by_project(
    task_id: str, coa_number: str, entitas: str, start_date: str, end_date: str
):
    progress = states.read_progress()

    csv_file_path = f"temp/{task_id}_{constants.get_transaksi_detail_by_project}.csv"

    project_ids = progress[task_id]["filenames"][constants.get_project_by_entitas]

    try:
        conn = db_pool.pool.connection()
        cursor = conn.cursor()
        chunk_size = 6000

        project_ids = pd.read_csv(
            project_ids, chunksize=chunk_size, header=None, skiprows=[0]
        )

        for project_id in project_ids:
            project_id_str = ",".join(f"'{id}'" for id in project_id[0].tolist())

        sql = f"""
        SELECT
            gl_transaksi.project_ProjectID,
            gl_transaksi.no_gl_transaksi,
            gl_transaksi.tanggal_transaksi,
            gl_transaksi_detail.keterangan,
            gl_transaksi_detail.debit,
            gl_transaksi_detail.kredit
        FROM gl_transaksi
        JOIN gl_transaksi_detail
            ON gl_transaksi.id = gl_transaksi_detail.transaksi_id
        WHERE gl_transaksi.company_CompanyID like %s
            AND gl_transaksi.status_lvl_1 = 1
            AND gl_transaksi.project_ProjectID IN ({project_id_str})
            AND gl_transaksi_detail.deleted_at IS NULL
            AND gl_transaksi_detail.coa = %s
            AND gl_transaksi.tanggal_transaksi BETWEEN %s AND %s
        ORDER BY gl_transaksi.tanggal_transaksi,gl_transaksi.no_gl_transaksi ASC
        """

        def sql_exec():
            cursor.execute(sql, (f"{entitas}%", coa_number, start_date, end_date))

        def writer_csv():
            writer_csv_helper.writer_csv_helper(chunk_size, csv_file_path, cursor)

        preparation_helper.preparation_helper(
            task_id=task_id,
            task_name=constants.get_transaksi_detail_by_project,
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
