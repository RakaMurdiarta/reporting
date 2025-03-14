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
            {"font_size": 12, "bold": True, "align": "center", "valign": "vcenter"}
        )

        # Set title and period
        ws.merge_range("A3:D3", "Buku Besar Tampil Per Project TJS Rekap", font_18_bold)
        ws.merge_range("A4:D4", f"Periode : {start_date} - {end_date}", font_14_bold)

        ws.write("A8", "Project", header_style)
        ws.write("B8", "Debit", header_style)
        ws.write("C8", "Kredit", header_style)
        ws.write("D8", "Saldo", header_style)

        row = 9  # Start from row 9
        sum_debit = 0
        sum_kredit = 0
        grand_total = 0

        # Call transform data
        grouped_df = transform(preparing_task_id)

        for _, data_row in grouped_df.iterrows():
            ws.write(f"A{row}", data_row["project_name"])
            ws.write(f"B{row}", data_row["debit"])
            ws.write(f"C{row}", data_row["kredit"])

            if coa_prefix in [1, 5, 6, 7, 8]:
                ws.write(f"D{row}", data_row["saldo_debit"])
            else:
                ws.write(f"D{row}", data_row["saldo_kredit"])
            sum_debit += data_row["debit"]
            sum_kredit += data_row["kredit"]
            row += 1
        grand_total = sum_debit + sum_kredit
        ws.write(f"D{row}", grand_total, bold)
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
