"""
Case 3 - Loan Repayment Vintage/Cohort generator.

Meniru struktur file Looker `bquxjob_*.csv` (159 kolom):
  ref_num, app_id, loan_amount, loan_paid_out_date, restruct_status, app_type,
  score_model, upfront_amount, provision_amount,
  lalu month_0..month_24 x {payment, payment_crm, payment_bank,
                            cumulative, cumulative_crm, cumulative_bank}

Logika payback:
  - tiap loan punya tenor & installment ~ loan_amount/tenor
  - membayar tiap bulan sampai lunas; sebagian loan "default" (berhenti bayar)
  - sumber CRM vs Bank sedikit berbeda (timing/pembulatan)

Output: repayment_vintage.csv.gz  (20k loans).
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(2025)
N = 20_000
MAX_M = 24

APP_TYPE = ["PDF loan", "SME loan", "Mobile loan"]
RESTRUCT = ["Non Restructured Loan", "Restructured Loan (NR)", "Restructured Loan (R)"]
SCORE_MODELS = ["TUNAIKU_MOBILE_BI_201904", "TUNAIKU_NO_MOBILE_BI_R_202306", "TUNAIKU_ZERO_PAYER_R_202210"]


def build():
    app_id = 8_000_000 + np.arange(N)
    ref_num = app_id * 10 + RNG.integers(0, 9, N)
    loan_amount = np.clip(np.round(RNG.lognormal(15.6, 0.55, N) / 1e5) * 1e5, 1e6, 5e7)
    paid_out = pd.to_datetime("2023-01-01") + pd.to_timedelta(RNG.integers(0, 900, N), unit="D")
    tenor = RNG.choice([6, 12, 18, 24], N, p=[0.2, 0.4, 0.25, 0.15])
    upfront = np.round(loan_amount * RNG.uniform(0.0, 0.05, N) / 1e4) * 1e4
    provision = np.round(loan_amount * RNG.uniform(0.0, 0.03, N) / 1e4) * 1e4
    default_month = np.where(RNG.random(N) < 0.18,
                             RNG.integers(1, MAX_M, N), 999)  # 18% default di bulan acak

    cols = {
        "ref_num": ref_num, "app_id": app_id, "loan_amount": loan_amount,
        "loan_paid_out_date": paid_out.strftime("%Y-%m-%d"),
        "restruct_status": RNG.choice(RESTRUCT, N, p=[0.8, 0.12, 0.08]),
        "app_type": RNG.choice(APP_TYPE, N, p=[0.7, 0.15, 0.15]),
        "score_model": RNG.choice(SCORE_MODELS, N),
        "upfront_amount": upfront, "provision_amount": provision,
    }

    installment = np.ceil(loan_amount / tenor / 1e3) * 1e3
    cum = np.zeros(N)
    cum_crm = np.zeros(N)
    cum_bank = np.zeros(N)
    for m in range(MAX_M + 1):
        pay = np.where((m >= 1) & (m <= tenor) & (m < default_month), installment, 0.0)
        # jangan overpay
        pay = np.minimum(pay, np.maximum(loan_amount - cum, 0))
        crm = np.round(pay * RNG.uniform(0.97, 1.0, N))
        bank = np.round(pay * RNG.uniform(0.97, 1.0, N))
        cum += pay; cum_crm += crm; cum_bank += bank
        cols[f"month_{m}_payment"] = pay
        cols[f"month_{m}_payment_crm"] = crm
        cols[f"month_{m}_payment_bank"] = bank
        cols[f"month_{m}_payment_cumulative"] = cum.copy()
        cols[f"month_{m}_payment_cumulative_crm"] = cum_crm.copy()
        cols[f"month_{m}_payment_cumulative_bank"] = cum_bank.copy()

    df = pd.DataFrame(cols)
    df.to_csv("repayment_vintage.csv.gz", index=False, compression="gzip")
    import os
    print("rows", len(df), "cols", df.shape[1], "MB",
          round(os.path.getsize("repayment_vintage.csv.gz") / 1e6, 2))
    print("default rate:", round((default_month < 999).mean(), 3))
    print(df[["loan_amount", "month_0_payment", "month_1_payment",
              "month_24_payment_cumulative"]].describe().round(0))


if __name__ == "__main__":
    build()
