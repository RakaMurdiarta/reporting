from pool import db_pool
import csv
import pymysql
import pandas as pd
from modules.report_buku_besar.queries.proyek_saat_mencetak.constant.index import (
    constants,
)
from utils import preparation_helper, writer_csv_helper


def get_saldo_awal_buku_besar_per_proyek_detail(
    task_id: str, coa_number: str, entitas: str, start_date: str, end_date: str
):

    csv_file_path = (
        f"temp/{task_id}_{constants.get_saldo_awal_buku_besar_per_proyek_detail}.csv"
    )

    try:
        conn = db_pool.pool.connection()
        cursor = conn.cursor()
        chunk_size = 6000
        if str(coa_number)[0] in ["1", "5", "6", "7", "8"]:
            saldo_column = "SUM(debit - kredit) AS Saldo"
        else:
            saldo_column = "SUM(kredit - debit) AS Saldo"

        sql = f"""
        SELECT
            gl_transaksi.project_ProjectID,
            {saldo_column}
        FROM gl_transaksi
        JOIN gl_transaksi_detail
            ON gl_transaksi.id = gl_transaksi_detail.transaksi_id
        WHERE gl_transaksi.company_CompanyID like %s
            AND gl_transaksi.status_lvl_1 = 1
            AND gl_transaksi_detail.deleted_at IS NULL
            AND gl_transaksi_detail.coa = %s
            AND gl_transaksi.tanggal_transaksi <= %s
        GROUP BY project_ProjectID
        """

        def sql_exec():
            cursor.execute(sql, (f"{entitas}%", coa_number, start_date))

        def writer_csv():
            writer_csv_helper.writer_csv_helper(chunk_size, csv_file_path, cursor)

        preparation_helper.preparation_helper(
            task_id=task_id,
            task_name=constants.get_saldo_awal_buku_besar_per_proyek_detail,
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
