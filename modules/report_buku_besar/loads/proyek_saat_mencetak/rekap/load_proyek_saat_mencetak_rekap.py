import xlsxwriter
from progress import states
from storages import coa_detail_saldo
from modules.report_buku_besar.processing.proyek_saat_mencetak.rekap.transform_report_proyek_saat_mencetak_rekap import (
    transform,
)


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

        font_12_bold = wb.add_format(
            {"font_size": 12, "bold": True, "align": "center", "valign": "vcenter"}
        )

        border_bold = wb.add_format(
            {
                "border": 1,
                "bold": True,
                "align": "center",
                "valign": "vcenter",
            }
        )

        border = wb.add_format({"border": 1})
        font_18_bold = wb.add_format(
            {"font_size": 18, "bold": True, "align": "center", "valign": "vcenter"}
        )
        font_14_bold = wb.add_format(
            {"font_size": 12, "bold": True, "align": "center", "valign": "vcenter"}
        )

        # Set title and period
        ws.merge_range(
            "A3:D3", "Buku Besar Konsolidasi Tampil Per Project Rekap TJS", font_18_bold
        )
        ws.merge_range("A4:D4", f"Periode : {start_date} - {end_date}", font_14_bold)
        ws.merge_range("A5:D5", f"COA : {coa_label}", font_12_bold)

        ws.write("A8", "PROJECT", header_style)
        ws.write("B8", "DEBIT", header_style)
        ws.write("C8", "KREDIT", header_style)
        ws.write("D8", "SALDO", header_style)

        row = 9  # Start from row 9
        sum_debit = 0
        sum_kredit = 0
        grand_total = 0
        saldo = 0
        # Call transform data
        grouped_df = transform(preparing_task_id)

        for _, data_row in grouped_df.iterrows():
            ws.write(f"A{row}", data_row["project_name"], border)
            ws.write(f"B{row}", data_row["debit"], border)
            ws.write(f"C{row}", data_row["kredit"], border)

            if int(coa_prefix) in [1, 4, 5, 6, 7, 8, 9]:
                saldo = data_row["debit"] - data_row["kredit"]
                ws.write(f"D{row}", saldo, border)
            else:
                saldo = data_row["kredit"] - data_row["debit"]
                ws.write(f"D{row}", saldo, border)
            sum_debit += data_row["debit"]
            sum_kredit += data_row["kredit"]
            grand_total += saldo
            row += 1

        row += 1
        ws.merge_range(f"A{row}:A{row+1}", "GRAND TOTAL", border_bold)
        ws.write(f"B{row}", "DEBET", border_bold)
        ws.write(f"B{row+1}", sum_debit, border_bold)
        ws.write(f"C{row}", "KREDIT", border_bold)
        ws.write(f"C{row+1}", sum_kredit, border_bold)
        ws.write(f"D{row}", "SALDO AKHIR", border_bold)
        final_total = grand_total + saldo_paling_awal
        ws.write(f"D{row+1}", final_total, border_bold)
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
