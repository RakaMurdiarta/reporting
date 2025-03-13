from pool import db_pool
import csv
import pymysql
from progress import states
from modules.report_buku_besar.queries.proyek_pada_vendor.constant.index import (
    constants,
)
from utils import preparation_helper, writer_csv_helper
import pandas as pd


def get_proyek_by_vendor_transaksi(
    task_id: str, coa_number: str, entitas: str, start_date: str, end_date: str
):
    progress = states.read_progress()
    # if str(coa_number)[0] in ["1", "5", "6", "7", "8"]:
    #     saldo_column = "SUM(debit - kredit) AS Saldo"
    # else:
    #     saldo_column = "SUM(kredit - debit) AS Saldo"

    progress[task_id]["coa_number"] = coa_number
    states.write_progress(progress)
    csv_file_path = f"temp/{task_id}_{constants.get_proyek_by_vendor_transaksi}.csv"

    vendors = progress[task_id]["filenames"][
        constants.get_company_vendors_proyek_pada_vendor
    ]
    try:
        conn = db_pool.pool.connection()
        cursor = conn.cursor()
        chunk_size = 6000
        company_vendor_ids = []
        company_vendors = pd.read_csv(
            vendors, chunksize=chunk_size, header=None, skiprows=[0]
        )

        for vendor_id in company_vendors:
            company_vendor_ids.extend(vendor_id[0].tolist())

        vendor_ids_str = ",".join(f"'{id}'" for id in company_vendor_ids)

        sql = f"""
        SELECT
            gl_transaksi_detail.debit,
            gl_transaksi_detail.kredit,
            gl_transaksi.project_ProjectID,
            gl_transaksi.company_vendor_id,
            projects.Name AS proyek,
            company.Name AS vendor
        FROM 	
            gl_transaksi
            INNER JOIN gl_transaksi_detail ON gl_transaksi.id = gl_transaksi_detail.transaksi_id
            INNER JOIN projects ON projects.ProjectID = gl_transaksi.project_ProjectID
            INNER JOIN company ON gl_transaksi.company_vendor_id = company.CompanyID
        WHERE gl_transaksi.company_CompanyID like %s
            AND gl_transaksi.status_lvl_1 = 1
            AND gl_transaksi.company_vendor_id IN ({vendor_ids_str})
            AND gl_transaksi_detail.deleted_at IS NULL
            AND gl_transaksi_detail.coa = %s
            AND gl_transaksi.tanggal_transaksi <= %s
        """

        def sql_exec():
            cursor.execute(sql, (f"{entitas}%", coa_number, end_date))

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
