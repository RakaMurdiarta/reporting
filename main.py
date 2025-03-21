from dotenv import load_dotenv

load_dotenv()
import pymysql
import csv
import threading
from pool import db_pool
from uuid import uuid4
import subprocess
import os
from fastapi.responses import FileResponse, JSONResponse
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, BackgroundTasks
from progress import states
from request.buku_besar_report_dto import DownloadDto, ProcessingDto
from fastapi.middleware.cors import CORSMiddleware
from modules.report_buku_besar.queries.vendor_saat_mencetak.detail import (
    buku_besar_transaksi_detail,
    get_transaksi_tanpa_vendor_detail,
    get_saldo_awal_per_vendor,
    get_vendors,
)

from modules.report_buku_besar.queries.vendor_saat_mencetak.rekap import (
    get_buku_besar_tanpa_vendor_rekap,
    get_transaksi_tanpa_vendor_rekap,
)
from modules.report_buku_besar.dtos.vendor_saat_mencetak_dto import (
    VendorSaatMencetakDto,
)
from modules.report_buku_besar.queries.vendor_saat_mencetak import get_saldo_paling_awal
from views.states import read_view, write_view
from modules.report_buku_besar.loads.vendor_saat_mencetak.detail import (
    load_vendor_saat_mencetak_detail,
)
from modules.report_buku_besar.loads.vendor_saat_mencetak.rekap import (
    load_vendor_saat_mencetak_rekap,
)
from views import states as view_state
from modules.report_buku_besar.dtos.proyek_pada_vendor_dto import ProyekPadaVendorDto
from modules.report_buku_besar.queries.proyek_pada_vendor.get_proyek_by_vendor import (
    get_proyek_by_vendor,
)
from modules.report_buku_besar.queries.proyek_pada_vendor.get_proyek_by_vendor_transaksi import (
    get_proyek_by_vendor_transaksi,
)
from modules.report_buku_besar.processing.proyek_pada_vendor.transform_proyek_pada_vendor import (
    transform,
)
from modules.report_buku_besar.loads.proyek_pada_vendor.load_proyek_pada_vendor import (
    load as load_proyek_pada_vendor,
)

from modules.report_buku_besar.queries.proyek_saat_mencetak.get_coa_detail_saldo import (
    get_coa_detail_saldo,
)
from modules.report_buku_besar.dtos.proyek_saat_mencetak_dto import (
    ProyekSaatMencetakDto,
)
from modules.report_buku_besar.queries.proyek_saat_mencetak.detail.get_poject_by_entitas import (
    get_project_by_entitas,
)
from modules.report_buku_besar.queries.proyek_saat_mencetak.rekap.get_transaksi_rekap_by_projects import (
    get_transaksi_rekap_by_projects,
)
from modules.report_buku_besar.queries.proyek_saat_mencetak.detail.get_transaksi_detail_by_project import (
    get_transaksi_detail_by_project,
)
from modules.report_buku_besar.queries.proyek_saat_mencetak.detail.get_saldo_awal_buku_besar_per_proyek_detail import (
    get_saldo_awal_buku_besar_per_proyek_detail,
)
from modules.report_buku_besar.processing.proyek_saat_mencetak.detail.transform_report_proyek_saat_mencetak_detail import (
    transform,
)
from modules.report_buku_besar.loads.proyek_saat_mencetak.detail import (
    load_proyek_saat_mencetak_detail,
)

from modules.report_buku_besar.loads.proyek_saat_mencetak.rekap import (
    load_proyek_saat_mencetak_rekap,
)

from storages import coa_detail_saldo


@asynccontextmanager
async def lifespan(app: FastAPI):

    # init base route
    baseRoute = APIRouter(prefix="/v1")

    @app.post(
        "/vendor_saat_mencetak/preparing", tags=["Vendor Saat Mencetak Reporting"]
    )
    async def preparing_vendor_saat_mencetak(
        payload: VendorSaatMencetakDto, background_tasks: BackgroundTasks
    ):
        # Menambahkan tugas ekspor ke background
        task_id = str(uuid4())
        views = read_view()
        store = coa_detail_saldo.read_coa_detail_saldo()
        if task_id not in store:
            store[task_id] = {}

        store[task_id]["coa_prefix"] = str(payload.coa_number)[0]
        store[task_id]["coa_label"] = payload.coa_label

        coa_detail_saldo.write_coa_detail_saldo(store)
        views[task_id] = payload.view

        background_tasks.add_task(
            get_saldo_paling_awal.get_saldo_paling_awal,
            task_id,
            payload.coa_number,
            payload.enititas,
        )

        if payload.view == 1:  # rekap
            background_tasks.add_task(
                get_transaksi_tanpa_vendor_rekap.get_transaksi_tanpa_vendor_rekap,
                task_id,
                payload.coa_number,
                payload.enititas,
                payload.start_date,
                payload.end_date,
            )

            background_tasks.add_task(
                get_buku_besar_tanpa_vendor_rekap.buku_besar_transaksi_tanpa_vendor,
                task_id,
                payload.coa_number,
                payload.enititas,
                payload.start_date,
                payload.end_date,
            )
        elif payload.view == 0:  # detail
            background_tasks.add_task(
                get_transaksi_tanpa_vendor_detail.transaksi_tanpa_vendor_detail,
                task_id,
                payload.coa_number,
                payload.enititas,
                payload.start_date,
                payload.end_date,
            )

            background_tasks.add_task(
                get_transaksi_tanpa_vendor_detail.get_saldo_awal_transaksi_tanpa_vendor_detail,
                task_id,
                payload.coa_number,
                payload.enititas,
                payload.start_date,
            )

            background_tasks.add_task(
                get_vendors.get_vendors,
                task_id,
                payload.coa_number,
                payload.enititas,
                payload.start_date,
                payload.end_date,
            )

            background_tasks.add_task(
                get_saldo_awal_per_vendor.get_saldo_awal_per_vendor,
                task_id,
                payload.coa_number,
                payload.enititas,
                payload.start_date,
                payload.end_date,
            )

            background_tasks.add_task(
                buku_besar_transaksi_detail.buku_besar_transaksi_detail,
                payload.enititas,
                payload.coa_number,
                payload.start_date,
                payload.end_date,
                task_id,
            )
        write_view(views=views)
        return {"message": "Preparing", "task_id": task_id}

    @app.post(
        "/vendor_saat_mencetak/processing", tags=["Vendor Saat Mencetak Reporting"]
    )
    async def processing_vendor_saat_mencetak(
        payload: ProcessingDto, background_tasks: BackgroundTasks
    ):
        task_id = str(uuid4())
        preparing_state = states.read_progress()
        view_state_temp = view_state.read_view()

        if preparing_state[payload.preparing_task_id]["status"] != "completed":
            return JSONResponse(content={"message": "cannot proccesing the data"})

        range_dates = preparing_state[payload.preparing_task_id]["range_date"]
        start_date = range_dates["start_date"]
        end_date = range_dates["end_date"]
        # Menambahkan tugas ekspor ke background
        __view = view_state_temp[payload.preparing_task_id]
        if __view == 0:
            expose_name = (
                f"{task_id}_report_buku_besar_{start_date}_{end_date}_detail.xlsx"
            )
        else:
            expose_name = (
                f"{task_id}_report_buku_besar_{start_date}_{end_date}_rekap.xlsx"
            )

        filename = f"temp/{expose_name}"
        background_tasks.add_task(
            run_script_vendor_saat_mencetak,
            task_id,
            payload.preparing_task_id,
            filename,
            __view,
        )

        return {"message": "Processing", "task_id": task_id, "file_name": expose_name}

    @app.post("/proyek_pada_vendor/preparing", tags=["Proyek Pada Vendor"])
    async def preparing_proyek_pada_vendor(
        payload: ProyekPadaVendorDto, background_tasks: BackgroundTasks
    ):

        task_id = str(uuid4())

        def in_order_exec():
            get_proyek_by_vendor(
                task_id,
                payload.coa_number,
                payload.enititas,
                payload.start_date,
                payload.end_date,
            )
            get_proyek_by_vendor_transaksi(
                task_id,
                payload.coa_number,
                payload.enititas,
                payload.start_date,
                payload.end_date,
            )

        background_tasks.add_task(in_order_exec)
        return {"message": "Preparing", "task_id": task_id}

    @app.post("/proyek_pada_vendor/processing", tags=["Proyek Pada Vendor"])
    async def processing_proyek_pada_vendor(
        payload: ProcessingDto, background_tasks: BackgroundTasks
    ):
        task_id = str(uuid4())

        preparing_state = states.read_progress()

        if preparing_state[payload.preparing_task_id]["status"] != "completed":
            return JSONResponse(content={"message": "cannot proccesing the data"})

        range_dates = preparing_state[payload.preparing_task_id]["range_date"]
        start_date = range_dates["start_date"]
        end_date = range_dates["end_date"]
        expose_name = (
            f"{task_id}_{start_date}_{end_date}_report_proyek_pada_vendor.xlsx"
        )
        filename = f"temp/{expose_name}"

        background_tasks.add_task(
            run_script_proyek_pada_vendor,
            task_id,
            payload.preparing_task_id,
            filename,
        )
        return {"message": "Processing", "task_id": task_id, "filename": expose_name}

    @app.post("/proyek_saat_mencetak/preparing", tags=["Proyek Saat Mencetak"])
    async def preparing_proyek_saat_mencetak(
        payload: ProyekSaatMencetakDto, background_tasks: BackgroundTasks
    ):
        try:
            task_id = str(uuid4())
            views = read_view()
            views[task_id] = payload.view
            get_coa_detail_saldo(task_id, payload.coa_number, payload.enititas)

            def in_order_exec():
                get_project_by_entitas(
                    task_id,
                    payload.coa_number,
                    payload.enititas,
                    payload.start_date,
                    payload.end_date,
                )
                get_transaksi_detail_by_project(
                    task_id,
                    payload.coa_number,
                    payload.enititas,
                    payload.start_date,
                    payload.end_date,
                )

                get_saldo_awal_buku_besar_per_proyek_detail(
                    task_id,
                    payload.coa_number,
                    payload.enititas,
                    payload.start_date,
                    payload.end_date,
                )

            if payload.view == 0:
                background_tasks.add_task(in_order_exec)
            else:
                background_tasks.add_task(
                    get_transaksi_rekap_by_projects,
                    task_id,
                    payload.coa_number,
                    payload.enititas,
                    payload.start_date,
                    payload.end_date,
                )

            write_view(views=views)
            return JSONResponse(
                content={"message": "Preparing", "task_id": task_id}, status_code=200
            )
        except Exception as e:
            print(e)
            return JSONResponse(
                content={"message": "Something went wrong"}, status_code=400
            )

    @app.post("/proyek_saat_mencetak/processing", tags=["Proyek Saat Mencetak"])
    async def processing_proyek_saat_mencetak(
        payload: ProcessingDto, background_tasks: BackgroundTasks
    ):
        task_id = str(uuid4())

        preparing_state = states.read_progress()
        view_state_temp = view_state.read_view()

        if preparing_state[payload.preparing_task_id]["status"] != "completed":
            return JSONResponse(content={"message": "cannot proccesing the data"})

        range_dates = preparing_state[payload.preparing_task_id]["range_date"]
        start_date = range_dates["start_date"]
        end_date = range_dates["end_date"]

        __view = view_state_temp[payload.preparing_task_id]

        if __view == 0:
            expose_name = f"{task_id}_report_buku_besar_proyek_saat_mencetak_{start_date}_{end_date}_detail.xlsx"
        else:
            expose_name = f"{task_id}_report_buku_besar_proyek_saat_mencetak_{start_date}_{end_date}_rekap.xlsx"

        filename = f"temp/{expose_name}"

        background_tasks.add_task(
            run_script_proyek_saat_mencetak,
            task_id,
            payload.preparing_task_id,
            filename,
            __view,
        )

        return {"message": "Processing", "task_id": task_id, "file_name": expose_name}

    @app.get("/download/{file_name}", tags=["Download"])
    async def download_file(file_name: str):
        # Tentukan path ke file yang akan didownload
        file_path = os.path.join("temp", file_name)

        # Periksa apakah file ada di server
        if os.path.exists(file_path):
            return FileResponse(
                file_path,
                media_type="application/octet-stream",
                headers={"Content-Disposition": f"attachment; filename={file_name}"},
            )
        else:
            return {"error": "File not found"}

    @app.get("/processing-status/{task_id}", tags=["Status"])
    async def checking_status_preparing(task_id: str):
        # Membaca status dari file JSON
        status_data = states.read_proccessing()

        if task_id in status_data:
            return JSONResponse(content={"status": status_data[task_id]["status"]})
        else:
            return JSONResponse(content={"message": "Task not found"}, status_code=404)

    @app.get("/preparing-status/{task_id}", tags=["Status"])
    async def checking_status_processing(task_id: str):
        # Membaca status dari file JSON
        status_data = states.read_progress()

        if task_id in status_data:
            return JSONResponse(content={"status": status_data[task_id]["status"]})
        else:
            return JSONResponse(content={"message": "Task not found"}, status_code=404)

    # register route as wrap parent route
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


def run_script_vendor_saat_mencetak(
    processing_task_id: str, preparing_task_id: str, filename: str, view: int
):
    if view == 0:
        load_vendor_saat_mencetak_detail.load(
            processing_task_id, preparing_task_id, filename
        )
    else:
        load_vendor_saat_mencetak_rekap.load(
            preparing_task_id, preparing_task_id, filename
        )


def run_script_proyek_pada_vendor(
    processing_task_id: str, preparing_task_id: str, filename: str
):
    load_proyek_pada_vendor(processing_task_id, preparing_task_id, filename)


def run_script_proyek_saat_mencetak(
    processing_task_id: str, preparing_task_id: str, filename: str, view: int
):
    if view == 0:
        load_proyek_saat_mencetak_detail.load(
            processing_task_id, preparing_task_id, filename
        )
    else:
        load_proyek_saat_mencetak_rekap.load(
            processing_task_id, preparing_task_id, filename
        )


# Untuk menjalankan server FastAPI dengan Uvicorn
# Uvicorn biasanya dijalankan dengan command seperti ini di terminal
# uvicorn main:app --reload
