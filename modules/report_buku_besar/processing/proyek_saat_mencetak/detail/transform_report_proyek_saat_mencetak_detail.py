import pandas as pd
from progress import states
from modules.report_buku_besar.queries.proyek_saat_mencetak.constant.index import (
    constants,
)


def transform(preparing_task_id: str):
    preparing_state = states.read_progress()

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

    df_merge_1 = pd.merge(
        df_transaksi_detail,
        project_details_name,
        on="project_ProjectID",
        how="left",
    )

    df_merge_final = pd.merge(
        df_merge_1,
        df_saldo_awal_buku_besar_per_proyek_detail,
        on="project_ProjectID",
        how="left",
    )

    db_export = df_merge_final[
        [
            "project_ProjectID",
            "Name",
            "tanggal_transaksi",
            "no_gl_transaksi",
            "keterangan",
            "debit",
            "kredit",
            "Saldo",
        ]
    ]

    grouped_df = db_export.groupby("project_ProjectID").apply(
        lambda x: x.reset_index(drop=True)
    )

    return grouped_df
