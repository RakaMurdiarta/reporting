import xlsxwriter
from progress import states
from modules.report_buku_besar.processing.vendor_saat_mencetak.detail import (
    transform_vendor_saat_mencetak_detail,
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

        # Define some formats
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
        font_18_bold = wb.add_format(
            {"font_size": 18, "bold": True, "align": "center", "valign": "vcenter"}
        )
        font_14_bold = wb.add_format(
            {"font_size": 14, "bold": True, "align": "center", "valign": "vcenter"}
        )

        # Set title and period
        ws.merge_range("A3:G3", "Buku Besar Tampil Per Vendor TJS Detail", font_18_bold)
        ws.merge_range("A4:G4", f"Periode : {start_date} - {end_date}", font_14_bold)

        # Write header in row 8
        ws.write("A8", "Name", header_style)
        ws.write("B8", "Tanggal Transaksi", header_style)
        ws.write("C8", "Bukti Transaksi", header_style)
        ws.write("D8", "Keterangan", header_style)
        ws.write("E8", "Debit", header_style)
        ws.write("F8", "Kredit", header_style)
        ws.write("G8", "Saldo", header_style)

        # to pin column
        # ws.freeze_panes(8, 7)

        # Write data to the worksheet
        row = 9  # Start from row 9
        total_sum = 0
        debit_sum = 0
        kredit_sum = 0
        saldo_awal_sum = 0
        # Call transform data
        grouped_df = transform_vendor_saat_mencetak_detail.transform(preparing_task_id)

        for company_id, group in grouped_df.groupby(level=0):
            name = group.iloc[0]["Name"]
            ws.write(f"A{row}", name, bold)
            row += 2  # Move to the next row
            saldo = row - 1
            saldo_awal = 0
            counting = 1
            saldo_cal = 0
            saldo_vendor_awal = 0
            for _, data_row in group.iterrows():
                debit = 0
                kredit = 0
                saldo_vendor_awal = (
                    data_row["Saldo"] if not pd.isna(data_row["Saldo"]) else 0
                )
                # Set the CoA number in the header
                if counting == 1:
                    saldo_awal = saldo_vendor_awal

                if not pd.isna(data_row["debit"]):
                    debit = data_row["debit"]

                if not pd.isna(data_row["kredit"]):
                    kredit = data_row["kredit"]

                # Handle calculation based on CoA prefix
                if data_row["coa_prefix"] in [1, 5, 6, 7, 8]:
                    ws.write(f"G{saldo}", saldo_vendor_awal)
                    saldo_cal = saldo_awal + debit - kredit
                    ws.write(f"G{row}", saldo_cal)
                else:
                    ws.write(f"G{saldo}", saldo_vendor_awal)
                    saldo_cal = saldo_awal + kredit - debit
                    ws.write(f"G{row}", saldo_cal)

                # Write transaction details
                ws.write(
                    f"B{row}",
                    (
                        data_row["tanggal_transaksi"]
                        if not pd.isna(data_row["tanggal_transaksi"])
                        else ""
                    ),
                )
                ws.write(
                    f"C{row}",
                    (
                        data_row["no_gl_transaksi"]
                        if not pd.isna(data_row["no_gl_transaksi"])
                        else ""
                    ),
                )
                ws.write(
                    f"D{row}",
                    (
                        data_row["keterangan"]
                        if not pd.isna(data_row["keterangan"])
                        else ""
                    ),
                )

                ws.write(f"E{row}", debit if not pd.isna(data_row["debit"]) else "")
                ws.write(f"F{row}", kredit if not pd.isna(data_row["kredit"]) else "")
                row += 1
                saldo_awal = saldo_cal
                counting += 1
                total_sum += saldo_cal
                debit_sum += debit
                kredit_sum += kredit
            saldo_awal_sum += saldo_vendor_awal

            saldo_awal = 0
            ws.write(f"F{row}", "Saldo Akhir", bold)
            ws.write(f"G{row}", saldo_cal)
            row += 1

        # Write total saldo
        ws.write(f"F{row + 1}", "Total Saldo", bold)
        ws.write(f"G{row + 1}", total_sum)
        ws.write(f"F{row + 2}", "Total Debit", bold)
        ws.write(f"G{row + 2}", debit_sum)
        ws.write(f"F{row + 3}", "Total Kredit", bold)
        ws.write(f"G{row + 3}", kredit_sum)
        ws.write(f"F{row + 4}", "Total Saldo Awal", bold)
        ws.write(f"G{row + 4}", saldo_awal_sum)

        if data_row["coa_prefix"] in [1, 5, 6, 7, 8]:
            grand_total = saldo_awal_sum + debit_sum - kredit_sum
        else:
            grand_total = saldo_awal_sum + kredit_sum - debit_sum

        ws.write(f"F{row + 5}", "Grand Total", bold)
        ws.write(f"G{row + 5}", grand_total)

        ws.autofit()

        # Save the file
        wb.close()

        print("Data has been processed and saved.")
        state_progres[processing_task_id]["status"] = "completed"
        states.write_proccessing(state_progres)

    except Exception as e:
        print(f"Error: {e}")
        state_progres[processing_task_id]["status"] = "failed"
        states.write_proccessing(state_progres)
        raise e
