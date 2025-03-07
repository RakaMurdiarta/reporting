import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

def proccess_data():
    df_saldo = pd.read_csv('saldo.csv')
    df_transaksi = pd.read_csv('transaksi.csv')

    # Menggabungkan data
    merged_df = pd.merge(df_transaksi, df_saldo, left_on='company_vendor_id', right_on='CompanyID', how='inner')

    # Menyiapkan data untuk diekspor
    db_export = merged_df[['CompanyID','tanggal_transaksi','no_gl_transaksi','keterangan', 'debit', 'kredit', 'Saldo', 'coa_prefix', 'coa', 'Name']]


    # Mengelompokkan berdasarkan CompanyID
    grouped_df = db_export.groupby("CompanyID")[["debit", "kredit","tanggal_transaksi",'no_gl_transaksi','keterangan','coa_prefix', 'Saldo', 'coa', 'Name']].apply(lambda x: x.reset_index(drop=True))

    # grouped_df.to_csv('ffff.csv',index=False)
    # return

    # Menulis ke Excel menggunakan openpyxl
    wb = Workbook()
    ws = wb.active
    ws.title = "Report"

    # Menambahkan title di cell E6
    ws['D3'] = "Report Summary"
    ws['D3'].font = Font(size=18, bold=True)
    ws['D3'].alignment = Alignment(horizontal='center', vertical='center')

    # Menulis header di row 8
    ws['A8'] = 'Name'
    ws['B8'] = 'Tanggal Transaksi'
    ws['C8'] = 'Bukti Transaksi'
    ws['D8'] = 'Keterangan'
    ws['E8'] = 'Debit'
    ws['F8'] = 'Kredit'
    ws['G8'] = 'Saldo'

    # Menulis data ke sheet dengan penyesuaian layout
    row = 9  # Mulai dari row 9
    for company_id, group in grouped_df.groupby(level=0):
        # print(group)
        # return
        name = group.iloc[0]['Name']
        ws[f'A{row}'] = name
        row += 2  # Pindah ke row berikutnya
        saldo = row - 1
        saldo_awal = 0
        counting = 1
        saldo_cal=0

        for _, data_row in group.iterrows():
            # ws[f'A{row - 2 }'] = data_row['Name']

            if counting == 1:
                saldo_awal = data_row['Saldo']

            ws['D4'] = f"Nomor Coa : {data_row['coa']}"
            ws['D4'].font = Font(size=18, bold=True)
            ws['D4'].alignment = Alignment(horizontal='center', vertical='center')

            # print(data_row['kredit'])
            # return
            if data_row['coa_prefix'] in [1, 5, 6, 7, 8]:
                ws[f'G{saldo}'] = data_row['Saldo']
                saldo_cal=saldo_awal + data_row['debit'] - data_row['kredit']
                ws[f'G{row}'] = saldo_cal
            else:
                ws[f'G{saldo}'] = data_row['Saldo']
                saldo_cal = saldo_awal + data_row['kredit'] - data_row['debit']
                ws[f'G{row}'] = saldo_cal
            ws[f'B{row}'] = data_row['tanggal_transaksi']
            ws[f'C{row}'] = data_row['no_gl_transaksi']
            ws[f'D{row}'] = data_row['keterangan']
            ws[f'E{row}'] = data_row['debit']
            ws[f'F{row}'] = data_row['kredit']
            row += 1
            saldo_awal=saldo_cal
            counting += 1
        saldo_awal = 0
        ws[f'G{row}'] = saldo_cal
        row+=1


    # Menambahkan style untuk header A8:C8
    header_cells = ws['A8:G8']  # Mengambil range sel header
    for cell in header_cells[0]:  # Iterasi untuk setiap cell dalam range header
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # Menyimpan file Excel
    wb.save("report_buku_besar_vendor.xlsx")
    print("Data has been processed and saved.")

proccess_data()
