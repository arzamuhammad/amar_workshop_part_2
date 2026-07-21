"""
Case 1 - Repeat Alarm: synthetic daily repeat-count data generator.

Menghasilkan 2 file:
  1. repeat_daily_count.csv          -> agregat harian TOTAL (untuk model utama), 1 series
  2. repeat_daily_count_segment.csv  -> harian per segmen (product x city x repeat_status)

Karakteristik deret waktu (menyerupai data asli Amar):
  - trend jangka panjang
  - weekly seasonality (akhir pekan lebih rendah)
  - yearly seasonality (musiman)
  - noise acak + sesekali lonjakan (campaign)

Tidak pakai faker. Hanya numpy + pandas (agar mudah direproduksi).
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

START = "2019-01-01"
END = "2026-07-31"

PRODUCTS = ["Tunaiku_PDF", "SMB_Loan", "Senyumku_Topup"]
CITIES = ["Jakarta", "Semarang", "Surabaya", "Bandung", "Medan"]
REPEAT_STATUS = ["New", "Repeat"]

# bobot relatif tiap dimensi (menentukan porsi volume)
PRODUCT_W = {"Tunaiku_PDF": 1.0, "SMB_Loan": 0.45, "Senyumku_Topup": 0.35}
CITY_W = {"Jakarta": 1.0, "Semarang": 0.55, "Surabaya": 0.7, "Bandung": 0.5, "Medan": 0.4}
STATUS_W = {"New": 1.0, "Repeat": 0.8}


def seasonal_series(dates: pd.DatetimeIndex, base: float, trend_per_year: float) -> np.ndarray:
    """Bangun deret dasar dengan trend + weekly + yearly seasonality."""
    n = len(dates)
    t = np.arange(n)
    years = t / 365.25
    trend = base + trend_per_year * years
    doy = dates.dayofyear.to_numpy()
    yearly = 1.0 + 0.18 * np.sin(2 * np.pi * doy / 365.25) + 0.08 * np.cos(4 * np.pi * doy / 365.25)
    dow = dates.dayofweek.to_numpy()  # 0=Mon..6=Sun
    weekly = np.where(dow >= 5, 0.62, 1.0)  # weekend lebih rendah
    weekly = weekly * (1.0 + 0.05 * np.sin(2 * np.pi * dow / 7))
    return trend * yearly * weekly


def add_noise_and_spikes(signal: np.ndarray) -> np.ndarray:
    noise = RNG.normal(1.0, 0.12, size=len(signal))
    out = signal * noise
    # campaign spikes ~1.5% hari
    spike_mask = RNG.random(len(signal)) < 0.015
    out = out + spike_mask * RNG.uniform(200, 700, size=len(signal))
    return np.clip(out, 20, None).round().astype(int)


def main():
    dates = pd.date_range(START, END, freq="D")

    # ---- Segmented series ----
    rows = []
    for p in PRODUCTS:
        for c in CITIES:
            for s in REPEAT_STATUS:
                base = 120 * PRODUCT_W[p] * CITY_W[c] * STATUS_W[s]
                trend = 30 * PRODUCT_W[p] * CITY_W[c]  # pertumbuhan/tahun
                sig = seasonal_series(dates, base=base, trend_per_year=trend)
                vals = add_noise_and_spikes(sig)
                seg = pd.DataFrame({
                    "created_date": dates.strftime("%Y-%m-%d"),
                    "product": p,
                    "city": c,
                    "repeat_status": s,
                    "repeat_count": vals,
                })
                rows.append(seg)
    df_seg = pd.concat(rows, ignore_index=True)

    # ---- Aggregate total per day (untuk model utama) ----
    df_total = (
        df_seg.groupby("created_date", as_index=False)["repeat_count"].sum()
        .sort_values("created_date")
        .reset_index(drop=True)
    )

    df_total.to_csv("repeat_daily_count.csv", index=False)
    df_seg.to_csv("repeat_daily_count_segment.csv", index=False)

    print("repeat_daily_count.csv        :", df_total.shape, "rows")
    print("repeat_daily_count_segment.csv:", df_seg.shape, "rows")
    print(df_total.head())
    print(df_total.tail())
    print("total repeat_count range:", df_total.repeat_count.min(), "-", df_total.repeat_count.max())


if __name__ == "__main__":
    main()
