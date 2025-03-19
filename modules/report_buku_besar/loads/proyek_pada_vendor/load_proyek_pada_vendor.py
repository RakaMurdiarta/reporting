import xlsxwriter
from progress import states
from modules.report_buku_besar.processing.proyek_pada_vendor.transform_proyek_pada_vendor import (
    transform,
)
import pandas as pd


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

        # Create a workbook and add a worksheet
        wb = xlsxwriter.Workbook(filename)
        ws = wb.add_worksheet("Report")

        bold = wb.add_format({"bold": True})
        header_style = wb.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "bg_color": "#A9D08E",  # Light green background
                "border": 1,
            }
        )

        border = wb.add_format({"border": 1})
        border_bold = wb.add_format({"border": 1, "bold": True})
        font_18_bold = wb.add_format(
            {"font_size": 18, "bold": True, "align": "center", "valign": "vcenter"}
        )

        font_14_bold = wb.add_format(
            {"font_size": 14, "bold": True, "align": "center", "valign": "vcenter"}
        )

        ws.merge_range(
            "A3:D3", "Buku Besar Tampil Vendor pada Proyek TJS", font_18_bold
        )
        ws.merge_range("A4:D4", f"Periode : {start_date} - {end_date}", font_14_bold)

        row = 11  # Start from row 10
        grand_total = 0
        df_proyek_pada_vendor_transaksi = transform(preparing_task_id)

        for _, group in df_proyek_pada_vendor_transaksi.groupby("company_vendor_id"):
            vendor_row = row - 1
            proyek_row = row - 2
            saldo_akhir = 0

            ws.write(f"A{proyek_row}", "Proyek", header_style)
            ws.write(f"B{proyek_row}", "Debit", header_style)
            ws.write(f"C{proyek_row}", "Kredit", header_style)
            ws.write(f"D{proyek_row}", "Saldo", header_style)

            for index, data_row in group.iterrows():
                ws.write(f"A{vendor_row}", data_row["Vendor"], bold)
                saldo = data_row["Saldo"] if not pd.isna(data_row["Saldo"]) else 0
                kredit = data_row["kredit"] if not pd.isna(data_row["kredit"]) else ""
                debit = data_row["debit"] if not pd.isna(data_row["debit"]) else ""
                (
                    ws.write(f"A{row}", data_row["proyek"])
                    if not pd.isna(data_row["proyek"])
                    else ws.write(f"A{row}", "")
                )
                ws.write(f"B{row}", debit)
                ws.write(f"C{row}", kredit)
                ws.write(f"D{row}", saldo)
                row += 1
                saldo_akhir += saldo
            # vendor_row
            grand_total += saldo_akhir
            ws.write(f"A{row}", "Saldo Akhir", bold)
            ws.write(f"D{row}", saldo_akhir, bold)
            row += 4

        ws.write(f"A{row}", "Grand Total", bold)
        ws.write(f"D{row}", grand_total, bold)
        ws.autofit()
        wb.close()
        print("Data has been processed and saved.")
        state_progres[processing_task_id]["status"] = "completed"
        states.write_proccessing(state_progres)
    except Exception as e:
        print(f"Error: {e}")
        state_progres[processing_task_id]["status"] = "failed"
        states.write_proccessing(state_progres)
        raise e
