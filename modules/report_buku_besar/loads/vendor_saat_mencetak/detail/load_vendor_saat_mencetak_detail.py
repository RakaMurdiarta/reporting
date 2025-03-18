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
        bold = wb.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
            }
        )
        bold_center = wb.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "border": 1,
            }
        )
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
        ws.write("E8", "Saldo Awal", header_style)
        ws.write("F8", "Debit", header_style)
        ws.write("G8", "Kredit", header_style)
        ws.write("H8", "Saldo", header_style)
        ws.write("I8", "Saldo Akhir", header_style)

        # to pin column
        # ws.freeze_panes(8, 7)

        # Write data to the worksheet
        row = 9  # Start from row 9
        debit_sum = 0
        kredit_sum = 0
        saldo_awal_sum = 0
        # Call transform data
        grouped_df, df_saldo_paling_awal = (
            transform_vendor_saat_mencetak_detail.transform(preparing_task_id)
        )

        saldo_paling_awal = (
            df_saldo_paling_awal.iloc[0]["saldo_paling_awal"]
            if not pd.isna(df_saldo_paling_awal.iloc[0]["saldo_paling_awal"])
            else 0
        )

        for company_id, group in grouped_df.groupby(level=0):
            merge_first_row = row
            name = group.iloc[0]["Name"]
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
                    # ws.write(f"H{saldo}", saldo_vendor_awal)
                    saldo_cal = saldo_awal + debit - kredit
                    ws.write(f"H{row}", saldo_cal)
                else:
                    # ws.write(f"H{saldo}", saldo_vendor_awal)
                    saldo_cal = saldo_awal + kredit - debit
                    ws.write(f"H{row}", saldo_cal)

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

                ws.write(f"F{row}", debit if not pd.isna(data_row["debit"]) else "")
                ws.write(f"G{row}", kredit if not pd.isna(data_row["kredit"]) else "")

                row += 1
                saldo_awal = saldo_cal
                counting += 1
                debit_sum += debit
                kredit_sum += kredit
            ws.merge_range(f"E{merge_first_row}:E{row}", saldo_vendor_awal, bold)
            ws.merge_range(f"I{merge_first_row}:I{row}", saldo_cal, bold)
            ws.merge_range(f"A{merge_first_row}:A{row}", name, bold)

            saldo_awal_sum += saldo_vendor_awal

            saldo_awal = 0
            # ws.write(f"F{row}", "Saldo Akhir", bold)
            # ws.write(f"G{row}", saldo_cal)
            row += 1
        ws.merge_range(f"D{row+3}:D{row+4}", "Grand Total", bold_center)
        ws.write(f"E{row+3}", "Total Saldo Awal", bold_center)
        ws.write(f"E{row+ 4}", saldo_awal_sum, bold_center)
        ws.write(f"F{row+3}", "Total Debit", bold_center)
        ws.write(f"F{row+ 4}", debit_sum, bold_center)
        ws.write(f"G{row+3}", "Total Kredit", bold_center)
        ws.write(f"G{row + 4}", kredit_sum, bold_center)

        if data_row["coa_prefix"] in [1, 5, 6, 7, 8]:
            grand_total = saldo_paling_awal + saldo_awal_sum + debit_sum - kredit_sum
        else:
            grand_total = saldo_paling_awal + saldo_awal_sum + kredit_sum - debit_sum

        ws.merge_range(f"H{row + 3}:I{row + 3}", "Total", bold_center)
        ws.merge_range(f"H{row + 4}:I{row + 4}", grand_total, bold_center)

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
