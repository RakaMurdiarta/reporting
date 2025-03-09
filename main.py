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
from progress import states
from request.buku_besar_report_dto import DownloadDto, PreparingDto,ProcessingDto
from fastapi.middleware.cors import CORSMiddleware



load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):


    #init base route
    baseRoute = APIRouter(prefix='/v1')

    @app.post("/preparing", tags=['Reporting'])
    async def preparing(payload: PreparingDto, background_tasks: BackgroundTasks):
        # Menambahkan tugas ekspor ke background
        task_id = str(uuid4())
        background_tasks.add_task(get_vendors_saldo.get_vendors_and_saldo, payload.enititas,payload.coa,payload.start_date,task_id)

        background_tasks.add_task(get_transaksi_vendor.get_transaksi_vendor, payload.enititas,payload.coa,payload.start_date,payload.end_date, task_id)
        
        return {"message": "Preparing", "task_id": task_id}

    @app.post("/processing",tags=['Reporting'])
    async def processing(payload: ProcessingDto,background_tasks: BackgroundTasks):
        task_id = str(uuid4())
        # Menambahkan tugas ekspor ke background
        filename= f'report_buku_besar_{payload.start_date}_{payload.end_date}.xlsx'
        background_tasks.add_task(run_script, task_id, payload.start_date,payload.end_date, filename)

        return {"message": "Processing", "task_id": task_id, "file_name": filename}


    @app.get("/download/{file_name}",tags=['Reporting'])
    async def download_file(file_name: str):
        # Tentukan path ke file yang akan didownload
        file_path = os.path.join("temp", file_name)

        # Periksa apakah file ada di server
        if os.path.exists(file_path):
            return FileResponse(file_path, media_type="application/octet-stream", headers={"Content-Disposition": f"attachment; filename={file_name}"})
        else:
            return {"error": "File not found"}
        
    @app.get("/processing-status/{task_id}",tags=['Reporting'])
    async def checking_status_preparing(task_id: str):
        # Membaca status dari file JSON
        status_data = states.read_proccessing()
        
        if task_id in status_data:
            return JSONResponse(content={'status': status_data[task_id]['status']})        
        else:
            return JSONResponse(content={"message": "Task not found"}, status_code=404)
        
    @app.get("/preparing-status/{task_id}",tags=['Reporting'])
    async def checking_status_processing(task_id: str):
        # Membaca status dari file JSON
        status_data = states.read_progress()
        
        if task_id in status_data:
            return JSONResponse(content={'status': status_data[task_id]['status']})
        else:
            return JSONResponse(content={"message": "Task not found"}, status_code=404)

    #register route as wrap parent route
    app.include_router(baseRoute)

    yield  


app = FastAPI(lifespan=lifespan)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_script(task_id: str, start_date:str, end_date: str, filename):
    proccessing_data.proccess_data(task_id, start_date, end_date,filename)

# Untuk menjalankan server FastAPI dengan Uvicorn
# Uvicorn biasanya dijalankan dengan command seperti ini di terminal
# uvicorn main:app --reload

