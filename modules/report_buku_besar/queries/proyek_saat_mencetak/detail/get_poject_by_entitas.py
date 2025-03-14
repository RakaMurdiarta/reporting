from pool import db_pool
import pymysql
from progress import states
from modules.report_buku_besar.queries.proyek_saat_mencetak.constant.index import (
    constants,
)
from utils import preparation_helper, writer_csv_helper


def get_project_by_entitas(
    task_id: str, coa_number: str, entitas: str, start_date: str, end_date: str
):
    progress = states.read_progress()

    states.write_progress(progress)

    csv_file_path = f"temp/{task_id}_{constants.get_project_by_entitas}.csv"

    try:
        conn = db_pool.pool.connection()
        cursor = conn.cursor()
        chunk_size = 6000

        sql = f"""
        SELECT
            DISTINCT(project_ProjectID) as project_ProjectID,
            projects.Name
        FROM gl_transaksi
        INNER JOIN gl_transaksi_detail
            ON gl_transaksi.id = gl_transaksi_detail.transaksi_id
        LEFT JOIN projects
                ON projects.ProjectID = gl_transaksi.project_ProjectID
        WHERE gl_transaksi.company_CompanyID like %s
                AND gl_transaksi.status_lvl_1 = 1
                AND gl_transaksi_detail.coa = %s
                AND gl_transaksi_detail.deleted_at IS NULL
        """

        def sql_exec():
            cursor.execute(sql, (f"{entitas}%", coa_number))

        def writer_csv():
            writer_csv_helper.writer_csv_helper(chunk_size, csv_file_path, cursor)

        preparation_helper.preparation_helper(
            task_id=task_id,
            task_name=constants.get_project_by_entitas,
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
