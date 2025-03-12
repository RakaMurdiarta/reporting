from openpyxl import Workbook
from openpyxl.styles import Font, Alignment
from progress import states
from modules.report_buku_besar.processing.vendor_saat_mencetak.detail import (
    transform_vendor_saat_mencetak_detail,
)


def load(processing_task_id: str, preparing_task_id: str, filename: str):
    try:
        state_progres = states.read_proccessing()
        preparing_state = states.read_progress()

        state_progres[processing_task_id] = {"status": "started"}
        states.write_proccessing(state_progres)
        state_progres[processing_task_id] = {"status": "process"}
        states.write_proccessing(state_progres)

        range_dates = preparing_state[preparing_task_id]["range_date"]
        start_date = range_dates["start_date"]
        end_date = range_dates["end_date"]

        wb = Workbook()
        ws = wb.active
        ws.title = "Report"

        # Menambahkan title di cell E6
        ws["D3"] = "Report Summary"
        ws["D3"].font = Font(size=18, bold=True)
        ws["D3"].alignment = Alignment(horizontal="center", vertical="center")
        ws["D5"] = f"Periode : {start_date} - {end_date}"
        ws["D5"].alignment = Alignment(horizontal="center", vertical="center")
        ws["D5"].font = Font(size=14, bold=True)

        # Menulis header di row 8
        ws["A8"] = "Name"
        ws["B8"] = "Tanggal Transaksi"
        ws["C8"] = "Bukti Transaksi"
        ws["D8"] = "Keterangan"
        ws["E8"] = "Debit"
        ws["F8"] = "Kredit"
        ws["G8"] = "Saldo"

        # Menulis data ke sheet dengan penyesuaian layout
        row = 9  # Mulai dari row 9
        sum = 0

        # call transform data
        grouped_df = transform_vendor_saat_mencetak_detail.transform(preparing_task_id)

        for company_id, group in grouped_df.groupby(level=0):
            name = group.iloc[0]["Name"]
            ws[f"A{row}"] = name
            row += 2  # Pindah ke row berikutnya
            saldo = row - 1
            saldo_awal = 0
            counting = 1
            saldo_cal = 0

            for _, data_row in group.iterrows():

                if counting == 1:
                    saldo_awal = data_row["Saldo"]

                ws["D4"] = f"Nomor Coa : {data_row['coa']}"
                ws["D4"].font = Font(size=18, bold=True)
                ws["D4"].alignment = Alignment(horizontal="center", vertical="center")

                # print(data_row['kredit'])
                # return
                if data_row["coa_prefix"] in [1, 5, 6, 7, 8]:
                    ws[f"G{saldo}"] = data_row["Saldo"]
                    saldo_cal = saldo_awal + data_row["debit"] - data_row["kredit"]
                    ws[f"G{row}"] = saldo_cal
                else:
                    ws[f"G{saldo}"] = data_row["Saldo"]
                    saldo_cal = saldo_awal + data_row["kredit"] - data_row["debit"]
                    ws[f"G{row}"] = saldo_cal
                ws[f"B{row}"] = data_row["tanggal_transaksi"]
                ws[f"C{row}"] = data_row["no_gl_transaksi"]
                ws[f"D{row}"] = data_row["keterangan"]
                ws[f"E{row}"] = data_row["debit"]
                ws[f"F{row}"] = data_row["kredit"]
                row += 1
                saldo_awal = saldo_cal
                counting += 1
                sum += saldo_cal
            saldo_awal = 0
            ws[f"F{row}"].font = Font(bold=True)
            ws[f"F{row}"] = "Saldo Akhir"
            ws[f"G{row}"] = saldo_cal
            row += 1

        ws[f"F{row+1}"].font = Font(bold=True)
        ws[f"F{row+1}"] = "Total Saldo"
        ws[f"G{row+1}"] = sum

        # Menambahkan style untuk header A8:C8
        header_cells = ws["A8:G8"]  # Mengambil range sel header
        for cell in header_cells[0]:  # Iterasi untuk setiap cell dalam range header
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")

        # Menyimpan file Excel
        wb.save(f"{filename}")
        print("Data has been processed and saved.")
        state_progres[processing_task_id]["status"] = "completed"
        states.write_proccessing(state_progres)
    except Exception as e:
        print(f"Error: {e}")
        state_progres[processing_task_id]["status"] = "failed"
        states.write_proccessing(state_progres)
