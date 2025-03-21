import pandas as pd
from modules.report_buku_besar.queries.vendor_saat_mencetak.constant.index import (
    constants,
)
from progress import states


def transform(preparing_task_id: str):
    preparing_state = states.read_progress()

    df_saldo_paling_awal = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][constants.get_saldo_paling_awal]
    )

    df_saldo_awal_tanpa_vendor = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.get_saldo_awal_transaksi_tanpa_vendor_detail
        ]
    )

    df_transaksi_tanpa_vendor = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.transaksi_tanpa_vendor_detail
        ]
    )

    df_vendors = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][constants.get_vendors]
    )

    df_saldo_awal_per_vendors = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.get_saldo_awal_per_vendor
        ]
    )

    df_saldo_per_vendors = pd.merge(
        df_vendors,
        df_saldo_awal_per_vendors,
        on="company_vendor_id",
        how="outer",
    )

    # df_saldo_per_vendors.to_csv("s.csv")

    df_buku_besar_transaksi = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.buku_besar_transaksi_detail
        ]
    )

    # pivot
    merged_df = pd.merge(
        df_buku_besar_transaksi,
        df_saldo_per_vendors,
        on="company_vendor_id",
        how="outer",
    )

    transform = merged_df.dropna(subset=["Saldo", "no_gl_transaksi"], how="all")

    db_export = transform[
        [
            "company_vendor_id",
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
    grouped_df = db_export.groupby("company_vendor_id")[
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

    return (
        grouped_df,
        df_saldo_paling_awal,
        df_saldo_awal_tanpa_vendor,
        df_transaksi_tanpa_vendor,
    )
