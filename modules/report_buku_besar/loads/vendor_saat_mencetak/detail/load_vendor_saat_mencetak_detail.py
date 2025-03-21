import xlsxwriter
from progress import states
from modules.report_buku_besar.processing.vendor_saat_mencetak.detail import (
    transform_vendor_saat_mencetak_detail,
)
import pandas as pd
from storages import coa_detail_saldo


def load(processing_task_id: str, preparing_task_id: str, filename: str):
    try:
        state_progres = states.read_proccessing()
        preparing_state = states.read_progress()
        store = coa_detail_saldo.read_coa_detail_saldo()
        coa_label = store[preparing_task_id]["coa_label"]
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

        # Set title and period
        ws.merge_range(
            "A3:G3", "Buku Besar Konsolidasi Tampil Per Vendor TJS Detail", font_18_bold
        )
        ws.merge_range("A4:G4", f"Periode : {start_date} - {end_date}", font_14_bold)

        ws.merge_range("A5:G5", f"COA : {coa_label}", font_12_bold)

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
            merge_saldo_awal = False
            # write header column
            for _, data_row in group.iterrows():
                coa_prefix = data_row["coa_prefix"]
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
                    ws.write(f"F{saldo_awal_row}", saldo_vendor_awal)
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
                        # ws.write(f"H{saldo}", saldo_vendor_awal)
                        saldo_cal = saldo_awal + kredit - debit
                        ws.write(f"F{row}", saldo_cal, border)
                saldo_awal = saldo_cal
                row += 1
                counting += 1
                debit_sum += debit
                kredit_sum += kredit

            ws.merge_range(f"A{row}:E{row}", "SALDO AKHIR", border_left)
            ws.write(f"F{row}", saldo_cal, border)

            saldo_awal_sum += saldo_vendor_awal
            row += 3

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
                ws.write(f"A{saldo_awal_row_tanpa_vendor}", "SALDO AWAL", bold_left)
                ws.write(f"F{saldo_awal_row_tanpa_vendor}", saldo_awal)

                if pd.isna(data_row["no_gl_transaksi"]):
                    if int(coa_prefix) in [1, 4, 5, 6, 7, 8, 9]:
                        # ws.write(f"H{saldo}", saldo_vendor_awal)
                        saldo_cal = (
                            saldo_awal + tanpa_vendor_debit - tanpa_vendor_kredit
                        )
                    else:
                        # ws.write(f"H{saldo}", saldo_vendor_awal)
                        saldo_cal = (
                            saldo_awal + tanpa_vendor_kredit - tanpa_vendor_debit
                        )
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
                            data_row["keterangan_transaksi"]
                            if not pd.isna(data_row["keterangan_transaksi"])
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

                    if int(coa_prefix) in [1, 4, 5, 6, 7, 8, 9]:
                        # ws.write(f"H{saldo}", saldo_vendor_awal)
                        saldo_cal = (
                            saldo_awal + tanpa_vendor_debit - tanpa_vendor_kredit
                        )
                        ws.write(f"F{row}", saldo_cal, border)
                    else:
                        # ws.write(f"H{saldo}", saldo_vendor_awal)
                        saldo_cal = (
                            saldo_awal + tanpa_vendor_kredit - tanpa_vendor_debit
                        )
                        ws.write(f"F{row}", saldo_cal, border)
                saldo_awal = saldo_cal
                row += 1
                saldo_awal_sum += saldo_awal_tanpa_vendor
                debit_sum += tanpa_vendor_debit
                kredit_sum += tanpa_vendor_kredit
            ws.write(f"A{row}", "SALDO AKHIR", bold_left)
            ws.write(f"F{row}", saldo_cal)

        ws.merge_range(f"A{row+2}:B{row+3}", "GRAND TOTAL", bold_center)
        ws.write(f"C{row+2}", "SALDO AWAL", bold_center)
        ws.write(f"C{row+ 3}", saldo_awal_sum, bold_center)
        ws.write(f"D{row+2}", "DEBET", bold_center)
        ws.write(f"D{row+ 3}", debit_sum, bold_center)
        ws.write(f"E{row+2}", "KREDIT", bold_center)
        ws.write(f"E{row + 3}", kredit_sum, bold_center)

        if int(coa_prefix) in [1, 4, 5, 6, 7, 8, 9]:
            grand_total = saldo_paling_awal + saldo_awal_sum + debit_sum - kredit_sum
        else:
            grand_total = saldo_paling_awal + saldo_awal_sum + kredit_sum - debit_sum

        ws.write(f"F{row+2}", "SALDO AKHIR", bold_center)
        ws.write(f"F{row + 3}", grand_total, bold_center)

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
