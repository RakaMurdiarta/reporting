from modules.report_buku_besar.processing.vendor_saat_mencetak.rekap import (
    transform_vendor_saat_mencetak_rekap,
)
from progress import states
import xlsxwriter
from storages import coa_detail_saldo
import pandas as pd


def load(processing_task_id: str, preparing_task_id: str, filename: str):
    # Create a workbook and add a worksheet
    try:
        store = coa_detail_saldo.read_coa_detail_saldo()
        coa_prefix = store[preparing_task_id]["coa_prefix"]
        coa_label = store[preparing_task_id]["coa_label"]
        wb = xlsxwriter.Workbook(filename)
        ws = wb.add_worksheet("Report")

        border = wb.add_format(
            {
                "border": 1,
            }
        )
        border_bold = wb.add_format(
            {
                "border": 1,
                "bold": True,
                "align": "center",
                "valign": "vcenter",
            }
        )

        # Adding a custom style with bold, center alignment, and border
        center_merged = wb.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "font_size": 18,
            }
        )

        center_merged_font_size_14 = wb.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "font_size": 14,
            }
        )
        center_merged_font_size_12 = wb.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
                "font_size": 12,
            }
        )

        # Adding a style for the header row with background color and bold text
        header_style = wb.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "bg_color": "#A9D08E",  # Light green background
                "border": 1,
            }
        )

        state_progres = states.read_proccessing()
        preparing_state = states.read_progress()
        state_progres[processing_task_id] = {"status": "started"}
        states.write_proccessing(state_progres)
        state_progres[processing_task_id] = {"status": "process"}
        states.write_proccessing(state_progres)
        range_dates = preparing_state[preparing_task_id]["range_date"]
        start_date = range_dates["start_date"]
        end_date = range_dates["end_date"]

        # Set header with bold text, alignment, background color, and border
        ws.write("A8", "VENDOR", header_style)
        ws.write("B8", "DEBET", header_style)
        ws.write("C8", "KREDIT", header_style)
        ws.write("D8", "SALDO", header_style)

        # Merge and apply custom center-aligned formatting with border
        ws.merge_range(
            "A3:D3", "Buku Besar Konsolidasi Tampil Per Vendor TJS Rekap", center_merged
        )
        ws.merge_range(
            "A4:D4", f"Periode : {start_date} - {end_date}", center_merged_font_size_14
        )
        ws.merge_range("A5:D5", f"COA : {coa_label}", center_merged_font_size_12)

        row = 9
        (
            buku_besar_transform_rekap,
            saldo_paling_awal,
            df_transaksi_tanpa_vendor_rekap,
        ) = transform_vendor_saat_mencetak_rekap.transform(preparing_task_id)

        total_saldo = 0
        total_debit = 0
        total_kredit = 0

        saldo_paling_awal_vendor = (
            saldo_paling_awal.iloc[0]["saldo_paling_awal"]
            if not pd.isna(saldo_paling_awal.iloc[0]["saldo_paling_awal"])
            else 0
        )

        # Write data to worksheet with borders and a default font style
        for index, data_row in buku_besar_transform_rekap.iterrows():
            ws.write(f"A{row}", data_row["Name"], border)
            ws.write(f"B{row}", data_row["debit"], border)
            ws.write(f"C{row}", data_row["kredit"], border)
            ws.write(f"D{row}", data_row["Saldo"], border)
            total_debit += data_row["debit"]
            total_kredit += data_row["kredit"]
            total_saldo += data_row["Saldo"]
            row += 1
        # ==== TRANSAKSI TANPA VENDOR ====
        saldo = 0

        for index, data_row in df_transaksi_tanpa_vendor_rekap.iterrows():
            debit = 0
            kredit = 0
            ws.write(f"A{row}", "TRANSAKSI TANPA VENDOR", border)

            if not pd.isna(data_row["debit"]):
                debit = data_row["debit"]

            if not pd.isna(data_row["kredit"]):

                kredit = data_row["kredit"]

            if str(coa_prefix) in ["1", "4", "5", "6", "7", "8", "9"]:
                saldo = debit - kredit
            else:
                saldo = kredit - debit
            ws.write(f"B{row}", debit, border)
            ws.write(f"C{row}", kredit, border)
            ws.write(f"D{row}", saldo, border)
            row += 1
            total_debit += debit
            total_kredit += kredit
            total_saldo += saldo

        for col in range(4):  # Apply border to columns A, B, C, D
            ws.set_column(col, col, 20)  # Set minimum width
            ws.autofit()

        row += 1
        ws.merge_range(f"A{row}:A{row+1}", "GRAND TOTAL", border_bold)
        ws.write(f"B{row}", "DEBET", border_bold)
        ws.write(f"B{row+1}", total_debit, border_bold)
        ws.write(f"C{row}", "KREDIT", border_bold)
        ws.write(f"C{row+1}", total_kredit, border_bold)
        ws.write(f"D{row}", "SALDO AKHIR", border_bold)
        grand_total = total_saldo + saldo_paling_awal_vendor
        ws.write(f"D{row+1}", grand_total, border_bold)

        wb.close()
    except Exception as e:
        print(f"Error: {e}")
        state_progres[processing_task_id]["status"] = "failed"
        states.write_proccessing(state_progres)
        raise e
