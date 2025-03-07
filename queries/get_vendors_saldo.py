from dbutils.pooled_db import PooledDB
import csv
from tqdm import tqdm
import pymysql
from pool import db_pool


def get_vendors_and_saldo(entitas, coa, start_date):
    # Define saldo calculation depending on COA prefix
    if str(coa)[0] in ['1', '5', '6', '7', '8']:
        saldo_column = "SUM(debit - kredit) AS Saldo"
    else:
        saldo_column = "SUM(kredit - debit) AS Saldo"

    sql = f"""
    SELECT
        company.CompanyID,
        company.Name AS Name,
        {saldo_column}
    FROM gl_transaksi
    JOIN gl_transaksi_detail
        ON gl_transaksi_detail.transaksi_id = gl_transaksi.id
    JOIN company
        ON company.CompanyID = gl_transaksi.company_vendor_id
    WHERE gl_transaksi.company_CompanyID LIKE %s
        AND gl_transaksi.status_lvl_1 = 1
        AND gl_transaksi_detail.coa = %s
        AND gl_transaksi_detail.deleted_at IS NULL
        AND gl_transaksi.tanggal_transaksi < %s
    GROUP BY company.CompanyID, company.Name
    """
    csv_file_path = 'temp/saldo.csv'

    try:
        conn = db_pool.pool.connection()
        cursor = conn.cursor()
        chunk_size = 6000
        cursor.execute(sql, (f"{entitas}%", coa, start_date))
        columns = [desc[0] for desc in cursor.description]

        # Open CSV file for writing
        with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(columns)  # Write the header

            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break  # Exit the loop when no more data is available
                writer.writerows(rows)  # Write the fetched rows

        cursor.close()
        conn.close()

        print(f"Data exported to {csv_file_path}")

    except pymysql.MySQLError as e:
        print(f"Error executing query: {e}")
        return None
    finally:
        # Ensure the connection is closed
        if conn:
            conn.close()
            db_pool.pool.close()
