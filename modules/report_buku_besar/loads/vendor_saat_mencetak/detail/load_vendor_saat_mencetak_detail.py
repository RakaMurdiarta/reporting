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
        bold_left = wb.add_format(
            {
                "bold": True,
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

        border = wb.add_format(
            {
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

        # to pin column
        # ws.freeze_panes(8, 7)

        # Write data to the worksheet
        row = 9  # Start from row 9
        debit_sum = 0
        kredit_sum = 0
        saldo_awal_sum = 0
        coa_prefix = 0
        # Call transform data
        (
            grouped_df,
            df_saldo_paling_awal,
            df_saldo_awal_tanpa_vendor,
            df_transaksi_tanpa_vendor,
        ) = transform_vendor_saat_mencetak_detail.transform(preparing_task_id)

        saldo_paling_awal = (
            df_saldo_paling_awal.iloc[0]["saldo_paling_awal"]
            if not pd.isna(df_saldo_paling_awal.iloc[0]["saldo_paling_awal"])
            else 0
        )
        saldo_awal_tanpa_vendor = (
            df_saldo_awal_tanpa_vendor.iloc[0]["Saldo"]
            if not pd.isna(df_saldo_awal_tanpa_vendor.iloc[0]["Saldo"])
            else 0
        )

        for company_id, group in grouped_df.groupby(level=0):
            name = group.iloc[0]["Name"]
            row += 2  # Move to the next row
            header_row = row - 2
            name_row = row - 3
            saldo_awal_row = row - 1
            saldo_awal = 0
            counting = 1
            saldo_cal = 0
            saldo_vendor_awal = 0
            skip_debit_kredit = False

            # write header column
            for _, data_row in group.iterrows():
                coa_prefix = data_row["coa_prefix"]
                if pd.isna(data_row["kredit"]) and pd.isna(data_row["debit"]):
                    skip_debit_kredit = True

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

                if coa_prefix in [1, 5, 6, 7, 8]:
                    saldo_cal = saldo_awal + debit - kredit
                    if not skip_debit_kredit:
                        ws.write(f"F{row}", saldo_cal, border)

                else:
                    # ws.write(f"H{saldo}", saldo_vendor_awal)
                    saldo_cal = saldo_awal + kredit - debit
                    if not skip_debit_kredit:
                        ws.write(f"F{row}", saldo_cal, border)

                ws.write(f"A{name_row}", name, bold_left)
                ws.write(f"A{header_row}", "TANGGAL", header_style)
                ws.write(f"B{header_row}", "NO BUKTI", header_style)
                ws.write(f"C{header_row}", "KETERANGAN", header_style)
                ws.write(f"D{header_row}", "DEBIT", header_style)
                ws.write(f"E{header_row}", "KREDIT", header_style)
                ws.write(f"F{header_row}", "SALDO", header_style)
                ws.write(f"A{saldo_awal_row}", "Saldo Awal", bold_left)
                ws.write(f"F{saldo_awal_row}", saldo_vendor_awal)
                # Write transaction details
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
                if not skip_debit_kredit:
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
                else:
                    continue
                saldo_awal = saldo_cal
                row += 1
                counting += 1
                debit_sum += debit
                kredit_sum += kredit
                skip_debit_kredit = False

            ws.write(f"F{row}", saldo_cal)
            saldo_awal_sum += saldo_vendor_awal
            row += 2

        row += 2
        # this is for transaksi tanpa vendor
        if not df_transaksi_tanpa_vendor.empty:
            vendor_count = 1
            for _, data_row in df_transaksi_tanpa_vendor.iterrows():
                tanpa_vendor_debit = 0
                tanpa_vendor_kredit = 0
                header_row_tanpa_vendor = row - 2
                name_row_tanpa_vendor = row - 3
                saldo_awal_row_tanpa_vendor = row - 1

                if vendor_count == 1:
                    saldo_awal = saldo_awal_tanpa_vendor

                if not pd.isna(data_row["debit"]):
                    tanpa_vendor_debit = data_row["debit"]

                if not pd.isna(data_row["kredit"]):
                    tanpa_vendor_kredit = data_row["kredit"]

                if coa_prefix in [1, 4, 5, 6, 7, 8, 9]:
                    # ws.write(f"H{saldo}", saldo_vendor_awal)
                    saldo_cal = saldo_awal + tanpa_vendor_debit - tanpa_vendor_kredit
                    ws.write(f"F{row}", saldo_cal, border)
                else:
                    # ws.write(f"H{saldo}", saldo_vendor_awal)
                    saldo_cal = saldo_awal + tanpa_vendor_kredit - tanpa_vendor_debit
                    ws.write(f"F{row}", saldo_cal, border)

                ws.write(
                    f"A{name_row_tanpa_vendor}",
                    "TRANSAKSI TANPA VENDOR",
                    bold_left,
                )
                ws.write(f"A{header_row_tanpa_vendor}", "TANGGAL", header_style)
                ws.write(f"B{header_row_tanpa_vendor}", "NO BUKTI", header_style)
                ws.write(f"C{header_row_tanpa_vendor}", "KETERANGAN", header_style)
                ws.write(f"D{header_row_tanpa_vendor}", "DEBIT", header_style)
                ws.write(f"E{header_row_tanpa_vendor}", "KREDIT", header_style)
                ws.write(f"F{header_row_tanpa_vendor}", "SALDO", header_style)
                ws.write(f"A{saldo_awal_row_tanpa_vendor}", "Saldo Awal", bold_left)
                ws.write(f"F{saldo_awal_row_tanpa_vendor}", saldo_awal)

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
                    tanpa_vendor_debit if not pd.isna(data_row["debit"]) else "",
                    border,
                )
                ws.write(
                    f"E{row}",
                    tanpa_vendor_kredit if not pd.isna(data_row["kredit"]) else "",
                    border,
                )
                saldo_awal = saldo_cal
                row += 1
                saldo_awal_sum += saldo_awal_tanpa_vendor
                debit_sum += tanpa_vendor_debit
                kredit_sum += tanpa_vendor_kredit
            ws.write(f"F{row}", saldo_cal)

        ws.merge_range(f"A{row+3}:B{row+4}", "GRAND TOTAL", bold_center)
        ws.write(f"C{row+3}", "SALDO AWAL", bold_center)
        ws.write(f"C{row+ 4}", saldo_awal_sum, bold_center)
        ws.write(f"D{row+3}", "DEBET", bold_center)
        ws.write(f"D{row+ 4}", debit_sum, bold_center)
        ws.write(f"E{row+3}", "KREDIT", bold_center)
        ws.write(f"E{row + 4}", kredit_sum, bold_center)

        if coa_prefix in [1, 4, 5, 6, 7, 8, 9]:
            grand_total = saldo_paling_awal + saldo_awal_sum + debit_sum - kredit_sum
        else:
            grand_total = saldo_paling_awal + saldo_awal_sum + kredit_sum - debit_sum

        ws.write(f"F{row + 3}", "SALDO AKHIR", bold_center)
        ws.write(f"F{row + 4}", grand_total, bold_center)

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
