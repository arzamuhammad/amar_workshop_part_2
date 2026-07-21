"""
Case 2 - Paid Rejection Datamart generator.

Menghasilkan datamart "open table" loan-origination Amar/Tunaiku dengan
SEMUA 326 kolom (persis skema `sample table datamart 1 baris.xlsx`), 100k
aplikasi selama 12 bulan terakhir.

- Kolom KUNCI (funnel, demografi, reject, score, geo) diisi nilai realistis
  & konsisten satu sama lain.
- Kolom sisanya diisi default sesuai tipe (mayoritas NULL, seperti data asli
  yang memang sparse).

Output: paid_rejection_datamart.csv.gz  (gzip agar muat di GitHub < 100MB).
Hanya butuh numpy + pandas.
"""
import json
import numpy as np
import pandas as pd

RNG = np.random.default_rng(7)
N = 100_000

# ---- kamus nilai ----------------------------------------------------------
CITIES = {
    "KOTA JAKARTA": (-6.2088, 106.8456, 50110),
    "KOTA SEMARANG": (-6.9932, 110.4203, 50276),
    "KOTA SURABAYA": (-7.2575, 112.7521, 60111),
    "KOTA BANDUNG": (-6.9175, 107.6191, 40111),
    "KOTA MEDAN": (3.5952, 98.6722, 20111),
    "KOTA MAKASSAR": (-5.1477, 119.4327, 90111),
    "KOTA YOGYAKARTA": (-7.7956, 110.3695, 55111),
    "KOTA DENPASAR": (-8.6705, 115.2126, 80111),
}
CITY_NAMES = list(CITIES.keys())
APP_TYPE = ["PDF loan", "SME loan", "Mobile loan"]
PURPOSE = ["Renovation", "Business", "Education", "Medical", "Wedding", "Electronics", "Others"]
OCCUPATION = ["Private employee", "Entrepreneur", "Civil servant", "Freelancer", "Unemployed"]
EDUCATION = ["High School", "Diploma", "Bachelor", "Master", "Elementary"]
MARITAL = ["Single", "Married", "Divorced"]
GENDER = ["Laki-laki", "Perempuan"]
RELIGION = ["Muslim", "Christian", "Catholic", "Hindu", "Buddhist"]
MEDIASOURCE = ["Organic", "Affiliate", "Paid Search", "Social", "Referral", "Other"]
REPEAT_STATUS = ["New", "Repeat"]
# reason ditolak (untuk yang Rejected)
REJECT_REASONS = {
    "Income": "Insufficient income",
    "Risk": "High risk score",
    "Age": "Age out of policy",
    "Unemployed": "Employment not verified",
    "Double": "Duplicate application",
    "Outside": "Outside coverage area",
    "Limit": "Over exposure limit",
    "Execution": "Execution/verification failed",
}
REJECT_KEYS = list(REJECT_REASONS.keys())

# tahap terjauh funnel + probabilitas
# Created -> Accepted -> Printed -> PaidOut ; atau Rejected/Dropoff/Pending
STAGE_P = {
    "PaidOut": 0.42, "Printed_NoPO": 0.06, "Accepted_NoPrint": 0.05,
    "Rejected": 0.33, "Dropoff": 0.09, "Pending": 0.05,
}


def main():
    schema = json.load(open("_schema326.json"))
    cols = [c for c, _ in schema]

    # ---- kolom identitas & tanggal ----
    created = pd.to_datetime("2025-08-01") + pd.to_timedelta(RNG.integers(0, 365, N), unit="D")
    created_ts = created + pd.to_timedelta(RNG.integers(0, 86400, N), unit="s")

    app_id = 28_000_000 + np.arange(N)
    ref_num = app_id * 10 + RNG.integers(0, 9, N)
    cust_id = 27_000_000 + RNG.integers(0, 5_000_000, N)

    stages = RNG.choice(list(STAGE_P), size=N, p=list(STAGE_P.values()))

    city = RNG.choice(CITY_NAMES, size=N, p=[0.30, 0.14, 0.16, 0.12, 0.10, 0.07, 0.06, 0.05])
    lat = np.array([CITIES[c][0] for c in city]) + RNG.normal(0, 0.05, N)
    lon = np.array([CITIES[c][1] for c in city]) + RNG.normal(0, 0.05, N)
    zip_ = np.array([CITIES[c][2] for c in city]) + RNG.integers(0, 80, N)

    loan_amt = np.clip(np.round(RNG.lognormal(15.6, 0.5, N) / 1e5) * 1e5, 1e6, 5e7)
    age = RNG.integers(19, 60, N)
    income = np.clip(np.round(RNG.lognormal(15.4, 0.45, N) / 1e5) * 1e5, 2e6, 5e7)
    pd_score = np.clip(RNG.beta(2, 5, N), 0.01, 0.99).round(4)
    fraud = np.clip(RNG.beta(1.5, 12, N), 0, 1).round(3)
    zero_payer = np.clip(RNG.beta(1.2, 20, N), 0, 1).round(3)

    is_paidout = stages == "PaidOut"
    is_accepted = np.isin(stages, ["PaidOut", "Printed_NoPO", "Accepted_NoPrint"])
    is_printed = np.isin(stages, ["PaidOut", "Printed_NoPO"])
    is_rejected = stages == "Rejected"
    is_dropoff = stages == "Dropoff"
    is_pending = stages == "Pending"

    # reject reason hanya untuk rejected
    rej_key = np.where(is_rejected, RNG.choice(REJECT_KEYS, size=N), None)

    def when(mask, base_days=0):
        out = pd.Series([pd.NaT] * N)
        idx = np.where(mask)[0]
        out.iloc[idx] = created_ts[idx] + pd.to_timedelta(RNG.integers(0, 3, len(idx)) + base_days, unit="D")
        return out

    accepted_dt = when(is_accepted)
    printed_dt = when(is_printed, 1)
    paid_dt = when(is_paidout, 2)
    rejected_dt = when(is_rejected, 1)

    # ---- bangun dict semua kolom (default None) ----
    data = {c: [None] * N for c in cols}

    def put(name, arr):
        if name not in data:
            return
        if isinstance(arr, (str, int, float, bool)) or arr is None:
            data[name] = [arr] * N
        else:
            vals = list(arr)
            assert len(vals) == N, f"{name} len {len(vals)} != {N}"
            data[name] = vals

    put("Cust_ID", cust_id); put("Ref_Num", ref_num); put("app_id", app_id)
    put("cust_hash", [f"h{RNG.integers(1e15):x}" for _ in range(N)])
    put("App_Type", RNG.choice(APP_TYPE, N, p=[0.7, 0.15, 0.15]))
    put("App_Status", np.where(is_rejected, "Rejected", "Normal"))
    put("Loan_Amount", loan_amt); put("initial_loan_amount", loan_amt); put("loan_saldo", np.where(is_paidout, loan_amt, 0))
    put("purpose", RNG.choice(PURPOSE, N))
    put("Created_Date", created.normalize()); put("Created_Timestamp", created_ts); put("Created_User", "CRM-System")
    put("Accepted_Date", accepted_dt.dt.normalize()); put("Accepted_Datetime", accepted_dt); put("Acc_User", np.where(is_accepted, "CRM-System", None))
    put("Printed_Date", printed_dt.dt.normalize()); put("printed_datetime", printed_dt); put("printed_user", np.where(is_printed, "CRM-System", None))
    put("Paid_Date", paid_dt.dt.normalize()); put("paid_Datetime", paid_dt)
    put("Rejected_Date", rejected_dt.dt.normalize()); put("Rejected_Datetime", rejected_dt); put("Rejected_User", np.where(is_rejected, "CRM-System", None))

    # counters
    put("Created_Cnt", np.ones(N, int))
    put("Acc_Cnt", is_accepted.astype(int))
    put("Printed_Cnt", is_printed.astype(int))
    put("Paid_Out_Cnt", is_paidout.astype(int))
    put("Rej_Cust_Cnt", is_rejected.astype(int))
    put("Rej_Cust_All_Cnt", is_rejected.astype(int))
    put("Dropoff_Cnt", is_dropoff.astype(int))
    put("Pending_Score_Cnt", is_pending.astype(int))
    # amount sums
    put("Created_Amount_Sum", loan_amt)
    put("Accepted_Amount_Sum", np.where(is_accepted, loan_amt, 0))
    put("Printed_Amount_Sum", np.where(is_printed, loan_amt, 0))
    put("Paid_Out_Amount_Sum", np.where(is_paidout, loan_amt, 0))
    put("Rej_Cust_Amount_Sum", np.where(is_rejected, loan_amt, 0))
    put("Dropoff_Amount_Sum", np.where(is_dropoff, loan_amt, 0))
    # kategori reject count (untuk rejected sesuai reason)
    for k in REJECT_KEYS:
        put(f"{k}_Apps_Cnt", ((rej_key == k)).astype(int))
        put(f"{k}_Apps_Amount_Sum", np.where(rej_key == k, loan_amt, 0))
    put("reject_reason", [REJECT_REASONS[k] if k else None for k in rej_key])
    put("reject_sub_reason", [f"{k}-sub" if k else None for k in rej_key])

    # demografi
    put("City_KTP", city); put("City_Housing", city)
    put("cust_age", age); put("cust_age_current", age)
    put("income", income); put("disposable_income", np.round(income * RNG.uniform(0.3, 0.6, N)))
    put("gender", RNG.choice(GENDER, N)); put("religion", RNG.choice(RELIGION, N))
    put("education", RNG.choice(EDUCATION, N)); put("marital_status", RNG.choice(MARITAL, N))
    put("Occupation", RNG.choice(OCCUPATION, N))
    put("num_of_dependants", RNG.integers(0, 5, N))
    put("Mediasource", RNG.choice(MEDIASOURCE, N)); put("Mediasource_original", RNG.choice(MEDIASOURCE, N))
    put("repeat_status", RNG.choice(REPEAT_STATUS, N, p=[0.6, 0.4])); put("repeat_status_crm", RNG.choice(REPEAT_STATUS, N))
    put("zip_code_ktp_last", zip_); put("zip_code_housing_last", zip_)
    put("area_tag", [c.replace("KOTA ", "") for c in city])
    put("acc_bank", "AMAR BANK")

    # scores
    put("selected_probability_of_default", pd_score)
    put("fraud_score", fraud); put("fraud_score_before_acc", fraud)
    put("zero_payer_score", zero_payer)
    put("score_model", "TUNAIKU_NO_MOBILE_BI_R_202306")
    put("Score_Type", RNG.choice(["HIT-HIT", "HIT-NOHIT", "NOHIT-NOHIT"], N))
    put("decision_type", RNG.choice(["Automatic", "Manual"], N, p=[0.8, 0.2]))
    put("period", RNG.choice([6, 12, 18, 24], N))
    put("interest", np.round(RNG.uniform(0.6, 0.9, N), 2))
    put("current_overdue", np.where(is_paidout, RNG.integers(0, 90, N) * (RNG.random(N) < 0.2), 0))
    put("highest_overdue", np.where(is_paidout, RNG.integers(0, 120, N) * (RNG.random(N) < 0.25), 0))

    # geo
    put("latitude_at_submit", lat.round(6)); put("longitude_at_submit", lon.round(6))
    put("suspicious_lat_long", np.where(RNG.random(N) < 0.03, "Yes", "No"))
    put("is_dropoff", np.where(is_dropoff, "Drop Off", "Not Drop Off"))
    put("is_active", np.where(is_paidout, "Active", "Not Active"))
    put("first_applied_status", np.where(RNG.random(N) < 0.6, "First Applied", "Repeat Applied"))
    put("restruct_status", "Non Restructured Loan")

    df = pd.DataFrame(data, columns=cols)
    df.to_csv("paid_rejection_datamart.csv.gz", index=False, compression="gzip")
    print("rows:", len(df), "cols:", df.shape[1])
    print("stage dist:\n", pd.Series(stages).value_counts())
    import os
    print("file MB:", round(os.path.getsize("paid_rejection_datamart.csv.gz") / 1e6, 1))


if __name__ == "__main__":
    main()
