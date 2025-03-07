import pymysql
import csv
from tqdm import tqdm  # Importing tqdm for the progress bar
import threading
from queries import get_vendors_saldo
from queries import get_transaksi_vendor
from pool import db_pool
from uuid import uuid4  
import subprocess
import os
from fastapi.responses import FileResponse,JSONResponse
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter,BackgroundTasks
from proccessing import proccessing_data
from progress import backgorund



load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):


    #init base route
    baseRoute = APIRouter(prefix='/v1')

    @app.get("/preparing")
    async def prepare(background_tasks: BackgroundTasks):
        # Menambahkan tugas ekspor ke background
        task_id = str(uuid4())
        background_tasks.add_task(get_vendors_saldo.get_vendors_and_saldo, 'TJS','2010101','2024-01-01')

        background_tasks.add_task(get_transaksi_vendor.get_transaksi_vendor, 'TJS','2010101','2024-01-01','2024-12-31', task_id)
        
        return {"message": "Export process started in the background", "task_id": task_id}

    @app.get("/processing")
    async def prepare(background_tasks: BackgroundTasks):
        task_id = str(uuid4())
        # Menambahkan tugas ekspor ke background
        background_tasks.add_task(run_script, task_id)
        
        return {"message": "Export process started in the background", "task_id": task_id}


    @app.get("/download/{file_name}")
    async def download_file(file_name: str):
        # Tentukan path ke file yang akan didownload
        file_path = os.path.join("", file_name)

        # Periksa apakah file ada di server
        if os.path.exists(file_path):
            return FileResponse(file_path, media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={file_name}"})
        else:
            return {"error": "File not found"}
        
    @app.get("/processing-status/{task_id}")
    async def task_status(task_id: str):
        # Membaca status dari file JSON
        status_data = backgorund.read_proccessing()
        
        if task_id in status_data:
            return JSONResponse(content=status_data[task_id])
        else:
            return JSONResponse(content={"message": "Task not found"}, status_code=404)
        
    @app.get("/preparing-status/{task_id}")
    async def task_status(task_id: str):
        # Membaca status dari file JSON
        status_data = backgorund.read_progress()
        
        if task_id in status_data:
            return JSONResponse(content=status_data[task_id])
        else:
            return JSONResponse(content={"message": "Task not found"}, status_code=404)

    #register route as wrap parent route
    app.include_router(baseRoute)

    yield  


app = FastAPI(lifespan=lifespan)

def run_script(task_id: str):
    proccessing_data.proccess_data(task_id)

# Untuk menjalankan server FastAPI dengan Uvicorn
# Uvicorn biasanya dijalankan dengan command seperti ini di terminal
# uvicorn main:app --reload