import pandas as pd
from progress import states
from modules.report_buku_besar.queries.proyek_saat_mencetak.constant.index import (
    constants,
)


def transform(preparing_task_id: str):
    preparing_state = states.read_progress()

    df_transaksi_rekap_by_project = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.get_transaksi_rekap_by_project
        ]
    )

    return df_transaksi_rekap_by_project
