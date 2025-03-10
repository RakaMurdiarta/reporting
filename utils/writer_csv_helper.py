import csv
import pymysql
from pool import db_pool
from progress import states

def writer_csv_helper(chunk_size: int, path: str, cursor):
    try:
        columns = [desc[0] for desc in cursor.description]

        with open(path, mode='w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(columns)
            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break  # Exit the loop when no more data is available
                writer.writerows(rows)
        cursor.close()
        print(f"Data exported to {path}")
    except Exception as e:
        print(f"Error executing query: {e}")
        return None
