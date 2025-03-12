import pandas as pd
from modules.report_buku_besar.queries.vendor_saat_mencetak.constant.index import (
    constants,
)
from progress import states


def transform(preparing_task_id: str):
    preparing_state = states.read_progress()

    df_vendors_saldo = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.get_vendors_and_saldo_detail
        ]
    )

    df_buku_besar_transaksi = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.buku_besar_transaksi_detail
        ]
    )

    # pivot
    merged_df = pd.merge(
        df_buku_besar_transaksi,
        df_vendors_saldo,
        left_on="company_vendor_id",
        right_on="CompanyID",
        how="inner",
    )

    db_export = merged_df[
        [
            "CompanyID",
            "tanggal_transaksi",
            "no_gl_transaksi",
            "keterangan",
            "debit",
            "kredit",
            "Saldo",
            "coa_prefix",
            "coa",
            "Name",
        ]
    ]

    # Mengelompokkan berdasarkan CompanyID
    grouped_df = db_export.groupby("CompanyID")[
        [
            "debit",
            "kredit",
            "tanggal_transaksi",
            "no_gl_transaksi",
            "keterangan",
            "coa_prefix",
            "Saldo",
            "coa",
            "Name",
        ]
    ].apply(lambda x: x.reset_index(drop=True))

    return grouped_df
