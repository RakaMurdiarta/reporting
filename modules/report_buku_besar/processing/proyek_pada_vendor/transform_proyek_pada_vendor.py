from progress import states
import pandas as pd
from modules.report_buku_besar.queries.proyek_pada_vendor.constant.index import (
    constants,
)

import numpy as np


def transform(preparing_task_id: str):
    preparing_state = states.read_progress()

    coa_number = preparing_state[preparing_task_id]["coa_number"]

    df_companies = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.get_company_vendors_proyek_pada_vendor
        ]
    )

    df_proyek_pada_vendor = pd.read_csv(
        preparing_state[preparing_task_id]["filenames"][
            constants.get_proyek_by_vendor_transaksi
        ]
    )

    df_merge = pd.merge(
        df_companies, df_proyek_pada_vendor, on="company_vendor_id", how="outer"
    )

    df_merge["debit"] = df_merge["debit"].fillna(0)
    df_merge["kredit"] = df_merge["kredit"].fillna(0)

    agg_sum_kredit_debit = (
        df_merge.groupby(["company_vendor_id", "proyek"])
        .agg({"debit": "sum", "kredit": "sum"})
        .reset_index()
    )

    if str(coa_number)[0] in ["1", "5", "6", "7", "8"]:
        agg_sum_kredit_debit["Saldo"] = (
            agg_sum_kredit_debit["debit"] - agg_sum_kredit_debit["kredit"]
        )
    else:
        agg_sum_kredit_debit["Saldo"] = (
            agg_sum_kredit_debit["kredit"] - agg_sum_kredit_debit["debit"]
        )
    agg_sum_kredit_debit = agg_sum_kredit_debit[
        ["company_vendor_id", "Saldo", "proyek", "kredit", "debit"]
    ]
    df_merge = df_merge[["company_vendor_id", "Vendor", "proyek"]]

    merging = pd.merge(
        df_merge, agg_sum_kredit_debit, on=["company_vendor_id", "proyek"], how="left"
    )

    unique = merging.drop_duplicates()
    return unique
