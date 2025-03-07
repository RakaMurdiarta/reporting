from fastapi import FastAPI, BackgroundTasks
import pymysql
import csv
from tqdm import tqdm  # Importing tqdm for the progress bar
import threading
from queries import get_vendors_saldo
from queries import get_transaksi_vendor
from pool import db_pool
from uuid import uuid4  


app = FastAPI()


# Fungsi untuk mengekspor data ke CSV
def export_to_csv():
    # Setup connection pool

    # Create a connection
    conn = db_pool.pool.connection()
    cursor = conn.cursor()

    # Set the chunk size for fetching rows
    chunk_size = 6000

    # Execute a count query to estimate total number of rows
    cursor.execute("SELECT COUNT(*) FROM gl_transaksi")
    total_rows = cursor.fetchone()[0]

    # Execute the select query to get the column names (required for writing header)
    cursor.execute("SELECT * FROM gl_transaksi")
    columns = [desc[0] for desc in cursor.description]

    # Open a CSV file to export the data
    csv_file_path = 'output.csv'

    # Open CSV file for writing
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        
        # Write the header
        writer.writerow(columns)

        # Calculate the number of chunks
        total_chunks = (total_rows // chunk_size) + 1
        
        # Create a progress bar
        with tqdm(total=total_chunks, desc="Exporting data", unit="chunk") as pbar:
            # Fetch data in chunks and write to the CSV file
            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break  # Exit the loop when no more data is available
                writer.writerows(rows)  # Write the fetched rows
                pbar.update(1)  # Update the progress bar by 1 chunk

    # Close the cursor and connection
    cursor.close()
    conn.close()

    print(f"Data exported to {csv_file_path}")


@app.get("/preparing")
async def prepare(background_tasks: BackgroundTasks):
    # Menambahkan tugas ekspor ke background
    task_id = str(uuid4())
    background_tasks.add_task(get_vendors_saldo.get_vendors_and_saldo, 'TJS','2010101','2024-01-01')

    background_tasks.add_task(get_transaksi_vendor.get_transaksi_vendor, 'TJS','2010101','2024-01-01','2024-12-31', task_id)
    
    return {"message": "Export process started in the background"}

@app.get("/processing")
async def prepare(background_tasks: BackgroundTasks):
    # Menambahkan tugas ekspor ke background
    task_id = str(uuid4())
    background_tasks.add_task(get_vendors_saldo.get_vendors_and_saldo, 'TJS','2010101','2024-01-01')

    background_tasks.add_task(get_transaksi_vendor.get_transaksi_vendor, 'TJS','2010101','2024-01-01','2024-12-31', task_id)
    
    return {"message": "Export process started in the background"}

# Untuk menjalankan server FastAPI dengan Uvicorn
# Uvicorn biasanya dijalankan dengan command seperti ini di terminal
# uvicorn main:app --reload
