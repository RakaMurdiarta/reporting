from progress import states
import pandas as pd
from modules.report_buku_besar.queries.proyek_pada_vendor.constant.index import (
    constants,
)


def transform(preparing_task_id: str):
    preparing_state = states.read_progress()

    coa_number = preparing_state[preparing_task_id]["coa_number"]

    df_proyek_pada_vendor = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.get_proyek_by_vendor_transaksi
        ]
    )

    df_proyek_pada_vendor = df_proyek_pada_vendor.groupby(
        ["vendor", "proyek"], as_index=False
    ).sum()

    if str(coa_number)[0] in ["1", "5", "6", "7", "8"]:
        df_proyek_pada_vendor["Saldo"] = (
            df_proyek_pada_vendor["debit"] - df_proyek_pada_vendor["kredit"]
        )
    else:
        df_proyek_pada_vendor["Saldo"] = (
            df_proyek_pada_vendor["kredit"] - df_proyek_pada_vendor["debit"]
        )

    df_proyek_pada_vendor = df_proyek_pada_vendor.groupby("vendor")[
        ["vendor", "proyek", "debit", "kredit", "Saldo"]
    ].apply(lambda x: x.reset_index(drop=True))

    return df_proyek_pada_vendor
