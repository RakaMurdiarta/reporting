import pandas as pd
from progress import states
from storages import coa_detail_saldo
from modules.report_buku_besar.queries.proyek_saat_mencetak.constant.index import (
    constants,
)
import numpy as np


def transform(preparing_task_id: str):
    preparing_state = states.read_progress()
    storage_coa = coa_detail_saldo.read_coa_detail_saldo()

    project_details_name = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.get_project_by_entitas
        ]
    )

    df_transaksi_detail = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.get_transaksi_detail_by_project
        ]
    )

    df_saldo_awal_buku_besar_per_proyek_detail = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.get_saldo_awal_buku_besar_per_proyek_detail
        ]
    )

    df_saldo_awal_buku_agg = (
        df_saldo_awal_buku_besar_per_proyek_detail.groupby("project_ProjectID")
        .agg({"debit": "sum", "kredit": "sum"})
        .reset_index()
    )

    coa_prefix = storage_coa[preparing_task_id]["coa_prefix"]

    if coa_prefix in ["1", "5", "6", "7", "8"]:
        df_saldo_awal_buku_agg["saldo_awal"] = (
            df_saldo_awal_buku_agg["debit"] - df_saldo_awal_buku_agg["kredit"]
        )
    else:
        df_saldo_awal_buku_agg["saldo_awal"] = (
            df_saldo_awal_buku_agg["kredit"] - df_saldo_awal_buku_agg["debit"]
        )

    df_saldo_awal_buku_agg = df_saldo_awal_buku_agg[["project_ProjectID", "saldo_awal"]]

    df_merge_1 = pd.merge(
        df_transaksi_detail,
        project_details_name,
        on="project_ProjectID",
        how="outer",
    )

    df_merge_final = pd.merge(
        df_merge_1,
        df_saldo_awal_buku_agg,
        on="project_ProjectID",
        how="outer",
    )

    transform = df_merge_final.dropna(
        subset=["saldo_awal", "no_gl_transaksi"], how="all"
    )

    db_export = transform[
        [
            "project_ProjectID",
            "Name",
            "tanggal_transaksi",
            "no_gl_transaksi",
            "keterangan",
            "debit",
            "kredit",
            "saldo_awal",
        ]
    ]

    grouped_df = db_export.groupby("project_ProjectID").apply(
        lambda x: x.reset_index(drop=True)
    )

    return grouped_df
