import xlsxwriter
from progress import states
from storages import coa_detail_saldo
from modules.report_buku_besar.processing.proyek_saat_mencetak.detail.transform_report_proyek_saat_mencetak_detail import (
    transform,
)
import pandas as pd


def load(processing_task_id: str, preparing_task_id: str, filename: str):
    try:
        state_progres = states.read_proccessing()
        preparing_state = states.read_progress()
        store = coa_detail_saldo.read_coa_detail_saldo()

        coa_prefix = store[preparing_task_id]["coa_prefix"]
        saldo_paling_awal = store[preparing_task_id]["saldo_paling_awal"]
        state_progres[processing_task_id] = {"status": "started"}
        states.write_proccessing(state_progres)
        state_progres[processing_task_id] = {"status": "process"}
        states.write_proccessing(state_progres)
        range_dates = preparing_state[preparing_task_id]["range_date"]
        start_date = range_dates["start_date"]
        end_date = range_dates["end_date"]

        wb = xlsxwriter.Workbook(filename)
        ws = wb.add_worksheet("Report")

        # Define some formats
        bold = wb.add_format({"bold": True})
        center = wb.add_format({"align": "center", "valign": "vcenter"})
        wrap = wb.add_format({"text_wrap": True})
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

        # Set title and period
        ws.merge_range("A3:G3", "Buku Besar Tampil Per Vendor TJS Detail", font_18_bold)
        ws.merge_range("A4:G4", f"Periode : {start_date} - {end_date}", font_14_bold)

        ws.write("A8", "Name", header_style)
        ws.write("B8", "Tanggal Transaksi", header_style)
        ws.write("C8", "Bukti Transaksi", header_style)
        ws.write("D8", "Keterangan", header_style)
        ws.write("E8", "Saldo Awal", header_style)
        ws.write("F8", "Debit", header_style)
        ws.write("G8", "Kredit", header_style)
        ws.write("H8", "Saldo", header_style)
        ws.write("I8", "Saldo Akhir", header_style)

        row = 9  # Start from row 9
        debit_sum = 0
        kredit_sum = 0
        saldo_awal_sum = 0

        # Call transform data
        grouped_df = transform(preparing_task_id)

        for company_id, group in grouped_df.groupby(level=0):
            merge_first_row = row
            name = group.iloc[0]["Name"]
            ws.write(f"A{row}", name, bold)
            row += 2  # Move to the next row
            saldo_awal = 0
            counting = 1
            saldo_cal = 0
            parse_saldo = 0

            for _, data_row in group.iterrows():
                debit = 0
                kredit = 0
                # Set the CoA number in the header
                parse_saldo = (
                    data_row["saldo_awal"] if not pd.isna(data_row["saldo_awal"]) else 0
                )

                if counting == 1:
                    saldo_awal = parse_saldo

                if not pd.isna(data_row["debit"]):
                    debit = data_row["debit"]

                if not pd.isna(data_row["kredit"]):
                    kredit = data_row["kredit"]

                if int(coa_prefix) in [1, 4, 5, 6, 7, 8, 9]:
                    saldo_cal = saldo_awal + debit - kredit
                    ws.write(f"H{row}", saldo_cal)
                else:
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
            ws.merge_range(f"E{merge_first_row}:E{row}", parse_saldo, bold)
            ws.merge_range(f"I{merge_first_row}:I{row}", saldo_cal, bold)
            ws.merge_range(f"A{merge_first_row}:A{row}", name, bold)

            saldo_awal_sum += parse_saldo

            saldo_awal = 0
            row += 1

        # Write total saldo
        ws.merge_range(f"D{row+3}:D{row+4}", "Grand Total", bold_center)
        ws.write(f"E{row+3}", "Total Saldo Awal", bold_center)
        ws.write(f"E{row+ 4}", saldo_awal_sum, bold_center)
        ws.write(f"F{row+3}", "Total Debit", bold_center)
        ws.write(f"F{row+ 4}", debit_sum, bold_center)
        ws.write(f"G{row+3}", "Total Kredit", bold_center)
        ws.write(f"G{row + 4}", kredit_sum, bold_center)

        if int(coa_prefix) in [1, 4, 5, 6, 7, 8, 9]:
            grand_total = (
                int(saldo_paling_awal) + saldo_awal_sum + debit_sum - kredit_sum
            )
        else:
            grand_total = (
                int(saldo_paling_awal) + saldo_awal_sum + kredit_sum - debit_sum
            )

        ws.merge_range(f"H{row + 3}:I{row + 3}", "Total Saldo Akhir", bold_center)
        ws.merge_range(f"H{row + 4}:I{row + 4}", grand_total, bold_center)

        ws.autofit()

        # Save the file
        wb.close()

        print("Data has been processed and saved.")
        state_progres[processing_task_id]["status"] = "completed"
    except Exception as e:
        print(f"Error: {e}")
        state_progres[processing_task_id]["status"] = "failed"
        states.write_proccessing(state_progres)
        raise e
