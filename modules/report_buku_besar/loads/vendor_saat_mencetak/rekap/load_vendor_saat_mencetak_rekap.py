from modules.report_buku_besar.processing.vendor_saat_mencetak.rekap import (
    transform_vendor_saat_mencetak_rekap,
)
from progress import states
import xlsxwriter


def load(processing_task_id: str, preparing_task_id: str, filename: str):
    # Create a workbook and add a worksheet
    try:
        wb = xlsxwriter.Workbook(filename)
        ws = wb.add_worksheet("Report")

        # Define some formats
        # bold = wb.add_format({"bold": True})
        # center = wb.add_format({"align": "center", "valign": "vcenter"})
        border = wb.add_format(
            {
                "border": 1,
            }
        )  # Border format

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
        ws.write("A8", "Vendor", header_style)
        ws.write("B8", "Debet", header_style)
        ws.write("C8", "Kredit", header_style)
        ws.write("D8", "Saldo", header_style)

        # Merge and apply custom center-aligned formatting with border
        ws.merge_range("A3:D3", "Buku Besar Tampil Per Vendor TJS Rekap", center_merged)
        ws.merge_range("A4:D4", f"Periode : {start_date} - {end_date}", center_merged)

        row = 8
        buku_besar_transform_rekap = transform_vendor_saat_mencetak_rekap.transform(
            preparing_task_id
        )

        # Write data to worksheet with borders and a default font style
        for index, data_row in buku_besar_transform_rekap.iterrows():
            ws.write(row, 0, data_row["Name"], border)
            ws.write(row, 1, data_row["debit"], border)
            ws.write(row, 2, data_row["kredit"], border)
            ws.write(row, 3, data_row["Saldo"], border)
            row += 1

        for col in range(4):  # Apply border to columns A, B, C, D
            ws.set_column(col, col, 20)  # Set minimum width
            ws.autofit()
        wb.close()
    except Exception as e:
        print(f"Error: {e}")
        state_progres[processing_task_id]["status"] = "failed"
        states.write_proccessing(state_progres)
        raise e
