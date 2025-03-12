from openpyxl import Workbook
from openpyxl.styles import Border, Side, Font, Alignment
from modules.report_buku_besar.processing.vendor_saat_mencetak.rekap import (
    transform_vendor_saat_mencetak_rekap,
)
from progress import states


def load(processing_task_id: str, preparing_task_id: str, filename: str):
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"
    state_progres = states.read_proccessing()
    preparing_state = states.read_progress()
    state_progres[processing_task_id] = {"status": "started"}
    states.write_proccessing(state_progres)
    state_progres[processing_task_id] = {"status": "process"}
    states.write_proccessing(state_progres)
    range_dates = preparing_state[preparing_task_id]["range_date"]
    start_date = range_dates["start_date"]
    end_date = range_dates["end_date"]

    # Set header
    ws["A8"] = "Vendor"
    ws["B8"] = "Debet"
    ws["C8"] = "Kredit"
    ws["D8"] = "Saldo"

    # Define border style
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    row = 9  # Start row from
    sum = 0

    buku_besar_transform_rekap = transform_vendor_saat_mencetak_rekap.transform(
        preparing_task_id
    )
    ws.merge_cells("A3:D3")
    ws["A3"] = "Buku Besar Konsolidasi Tampil Per Vendor TJS Rekap"
    ws["A3"].font = Font(size=18, bold=True)
    ws["A3"].alignment = Alignment(horizontal="center", vertical="center")

    ws["C4"] = f"Periode : {start_date} - {end_date}"
    ws["C4"].alignment = Alignment(horizontal="center", vertical="center")
    ws["C4"].font = Font(size=14, bold=True)

    # Menulis data ke worksheet
    for index, data_row in buku_besar_transform_rekap.iterrows():
        ws[f"A{row}"] = data_row["Name"]
        ws[f"B{row}"] = data_row["debit"]
        ws[f"C{row}"] = data_row["kredit"]
        ws[f"D{row}"] = data_row["Saldo"]
        for col in ["A", "B", "C", "D"]:
            cell = ws[f"{col}{row}"]
            cell.border = thin_border
        row += 1
    header_cells = ws["A8:D8"]
    for cell in header_cells[0]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    wb.save(f"{filename}")
