import pandas as pd
from modules.report_buku_besar.queries.vendor_saat_mencetak.constant.index import (
    constants,
)
from progress import states


def transform(preparing_task_id: str):
    preparing_state = states.read_progress()

    df_rekap_group_by_company_vendor = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.buku_besar_transaksi_tanpa_vendor_rekap
        ]
    )

    saldo_paling_awal = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][constants.get_saldo_paling_awal]
    )

    df_transaksi_tanpa_vendor_rekap = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.get_transaksi_tanpa_vendor_rekap
        ]
    )

    return (
        df_rekap_group_by_company_vendor,
        saldo_paling_awal,
        df_transaksi_tanpa_vendor_rekap,
    )
