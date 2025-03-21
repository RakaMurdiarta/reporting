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
        coa_label = store[preparing_task_id]["coa_label"]
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
        font_12_bold = wb.add_format(
            {"font_size": 12, "bold": True, "align": "center", "valign": "vcenter"}
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
        bold_left = wb.add_format(
            {
                "bold": True,
            }
        )

        border_left = wb.add_format(
            {
                "bold": True,
                "border": 1,
            }
        )

        border = wb.add_format(
            {
                "border": 1,
            }
        )

        # Set title and period
        ws.merge_range("A3:G3", "BUKU BESAR TAMPIL PER PROYEK DETAIL", font_18_bold)
        ws.merge_range("A4:G4", f"Periode : {start_date} - {end_date}", font_14_bold)
        ws.merge_range("A5:G5", f"COA : {coa_label}", font_12_bold)

        row = 9  # Start from row 9
        debit_sum = 0
        kredit_sum = 0
        saldo_awal_sum = 0

        # Call transform data
        grouped_df = transform(preparing_task_id)

        for company_id, group in grouped_df.groupby(level=0):
            name = group.iloc[0]["Name"]
            ws.write(f"A{row}", name, bold)
            row += 2  # Move to the next row
            header_row = row - 2
            name_row = row - 3
            saldo_awal_row = row - 1
            saldo_awal = 0
            counting = 1
            saldo_cal = 0
            parse_saldo = 0
            merge_saldo_awal = False

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

                    # =======start write to excel ==============
                ws.write(f"A{name_row}", name, bold_left)
                ws.write(f"A{header_row}", "TANGGAL", header_style)
                ws.write(f"B{header_row}", "NO BUKTI", header_style)
                ws.write(f"C{header_row}", "KETERANGAN", header_style)
                ws.write(f"D{header_row}", "DEBIT", header_style)
                ws.write(f"E{header_row}", "KREDIT", header_style)
                ws.write(f"F{header_row}", "SALDO", header_style)

                if not merge_saldo_awal:
                    ws.merge_range(
                        f"A{saldo_awal_row}:E{saldo_awal_row}",
                        "SALDO AWAL",
                        border_left,
                    )
                    ws.write(f"F{saldo_awal_row}", parse_saldo)
                    merge_saldo_awal = True

                if pd.isna(data_row["no_gl_transaksi"]):
                    if int(coa_prefix) in [1, 4, 5, 6, 7, 8, 9]:
                        saldo_cal = saldo_awal + debit - kredit
                    else:
                        saldo_cal = saldo_awal + kredit - debit
                    continue
                else:
                    ws.write(
                        f"A{row}",
                        (
                            data_row["tanggal_transaksi"]
                            if not pd.isna(data_row["tanggal_transaksi"])
                            else ""
                        ),
                        border,
                    )
                    ws.write(
                        f"B{row}",
                        (
                            data_row["no_gl_transaksi"]
                            if not pd.isna(data_row["no_gl_transaksi"])
                            else ""
                        ),
                        border,
                    )
                    ws.write(
                        f"C{row}",
                        (
                            data_row["keterangan"]
                            if not pd.isna(data_row["keterangan"])
                            else ""
                        ),
                        border,
                    )

                    ws.write(
                        f"D{row}",
                        debit if not pd.isna(data_row["debit"]) else "",
                        border,
                    )
                    ws.write(
                        f"E{row}",
                        kredit if not pd.isna(data_row["kredit"]) else "",
                        border,
                    )

                    if int(coa_prefix) in [1, 4, 5, 6, 7, 8, 9]:
                        saldo_cal = saldo_awal + debit - kredit
                        ws.write(f"F{row}", saldo_cal, border)
                    else:
                        saldo_cal = saldo_awal + kredit - debit
                        ws.write(f"F{row}", saldo_cal, border)

                # Write transaction details

                saldo_awal = saldo_cal
                row += 1
                counting += 1
                debit_sum += debit
                kredit_sum += kredit

            ws.merge_range(f"A{row}:E{row}", "SALDO AKHIR", border_left)
            ws.write(f"F{row}", saldo_cal, border)

            saldo_awal_sum += parse_saldo
            row += 3

        row += 2
        # Write total saldo
        ws.merge_range(f"A{row+2}:B{row+3}", "GRAND TOTAL", bold_center)
        ws.write(f"C{row+2}", "SALDO AWAL", bold_center)
        ws.write(f"C{row+ 3}", saldo_awal_sum, bold_center)
        ws.write(f"D{row+2}", "DEBET", bold_center)
        ws.write(f"D{row+ 3}", debit_sum, bold_center)
        ws.write(f"E{row+2}", "KREDIT", bold_center)
        ws.write(f"E{row + 3}", kredit_sum, bold_center)

        if int(coa_prefix) in [1, 4, 5, 6, 7, 8, 9]:
            grand_total = (
                int(saldo_paling_awal) + saldo_awal_sum + debit_sum - kredit_sum
            )
        else:
            grand_total = (
                int(saldo_paling_awal) + saldo_awal_sum + kredit_sum - debit_sum
            )

        ws.write(f"F{row+2}", "SALDO AKHIR", bold_center)
        ws.write(f"F{row + 3}", grand_total, bold_center)

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
