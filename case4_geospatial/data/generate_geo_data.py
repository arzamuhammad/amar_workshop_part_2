"""
Case 4 — Geospatial (Digital Bank) data generator.
Amar Bank Workshop Part 2.

Menghasilkan 3 tabel (CSV) untuk analisa geospatial FSI:
  1. customers_geo.csv        - 10.000 nasabah (lat/long domisili, income, produk, default_flag)
  2. service_points.csv       - 200 titik layanan (ATM / Cabang / Agen Senyumku)
  3. loan_applications_geo.csv - 15.000 aplikasi (lokasi submit + timestamp) dengan
                                 skenario fraud (cluster titik sama + impossible travel)

Kota-kota Indonesia real (Jabodetabek + Semarang + kota besar lain).
Hanya numpy + pandas.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(99)

# (nama, lat, lon, bobot populasi)
CITIES = [
    ("Jakarta",   -6.2088, 106.8456, 0.34),
    ("Bogor",     -6.5950, 106.8166, 0.08),
    ("Depok",     -6.4025, 106.7942, 0.07),
    ("Tangerang", -6.1783, 106.6319, 0.09),
    ("Bekasi",    -6.2383, 106.9756, 0.09),
    ("Semarang",  -6.9932, 110.4203, 0.11),
    ("Surabaya",  -7.2575, 112.7521, 0.10),
    ("Bandung",   -6.9175, 107.6191, 0.07),
    ("Medan",      3.5952,  98.6722, 0.05),
]
NAMES = [c[0] for c in CITIES]
W = np.array([c[3] for c in CITIES]); W = W / W.sum()
PRODUCTS = ["Tunaiku_PDF", "SMB_Loan", "Senyumku_Savings"]
SP_TYPES = ["ATM", "Branch", "Agen"]


def jitter(lat, lon, n, scale=0.06):
    return lat + RNG.normal(0, scale, n), lon + RNG.normal(0, scale, n)


def gen_customers(n=10_000):
    idx = RNG.choice(len(CITIES), n, p=W)
    lat = np.array([CITIES[i][1] for i in idx])
    lon = np.array([CITIES[i][2] for i in idx])
    lat, lon = jitter(lat, lon, n)
    return pd.DataFrame({
        "customer_id": np.arange(1, n + 1),
        "city": [NAMES[i] for i in idx],
        "latitude": lat.round(6),
        "longitude": lon.round(6),
        "product": RNG.choice(PRODUCTS, n, p=[0.6, 0.2, 0.2]),
        "income": np.clip(np.round(RNG.lognormal(15.4, 0.45, n) / 1e5) * 1e5, 2e6, 5e7),
        "default_flag": (RNG.random(n) < 0.12).astype(int),
    })


def gen_service_points(n=200):
    idx = RNG.choice(len(CITIES), n, p=W)
    lat = np.array([CITIES[i][1] for i in idx])
    lon = np.array([CITIES[i][2] for i in idx])
    lat, lon = jitter(lat, lon, n, scale=0.05)
    return pd.DataFrame({
        "service_point_id": np.arange(1, n + 1),
        "sp_type": RNG.choice(SP_TYPES, n, p=[0.5, 0.2, 0.3]),
        "city": [NAMES[i] for i in idx],
        "latitude": lat.round(6),
        "longitude": lon.round(6),
    })


def gen_applications(customers, n=15_000):
    """Aplikasi dengan lokasi submit. Sisipkan skenario fraud."""
    cust = customers.sample(n, replace=True, random_state=1).reset_index(drop=True)
    lat = cust.latitude.to_numpy() + RNG.normal(0, 0.01, n)
    lon = cust.longitude.to_numpy() + RNG.normal(0, 0.01, n)
    ts = pd.to_datetime("2026-01-01") + pd.to_timedelta(RNG.integers(0, 180 * 24 * 3600, n), unit="s")

    df = pd.DataFrame({
        "app_id": np.arange(1, n + 1),
        "customer_id": cust.customer_id.to_numpy(),
        "submit_ts": ts,
        "latitude": lat,
        "longitude": lon,
        "loan_amount": np.clip(np.round(RNG.lognormal(15.6, 0.5, n) / 1e5) * 1e5, 1e6, 5e7),
    })

    # --- FRAUD 1: cluster titik sama (fraud ring) --- 40 aplikasi di 1 titik persis
    ring_lat, ring_lon = -6.2100, 106.8460  # sebuah titik di Jakarta
    ring_idx = RNG.choice(n, 40, replace=False)
    df.loc[ring_idx, "latitude"] = ring_lat + RNG.normal(0, 0.0002, 40)
    df.loc[ring_idx, "longitude"] = ring_lon + RNG.normal(0, 0.0002, 40)

    # --- FRAUD 2: impossible travel --- customer yg sama, 2 aplikasi jauh & selang <2 jam
    imp_cust = RNG.choice(customers.customer_id, 30, replace=False)
    extra = []
    for cid in imp_cust:
        base = df[df.customer_id == cid].head(1)
        if len(base) == 0:
            continue
        t0 = base.submit_ts.iloc[0]
        extra.append({
            "app_id": len(df) + len(extra) + 1,
            "customer_id": cid,
            "submit_ts": t0 + pd.Timedelta(minutes=int(RNG.integers(20, 110))),
            "latitude": 3.5952 + RNG.normal(0, 0.02),   # Medan (jauh)
            "longitude": 98.6722 + RNG.normal(0, 0.02),
            "loan_amount": 1e7,
        })
    df = pd.concat([df, pd.DataFrame(extra)], ignore_index=True)
    df["submit_ts"] = df["submit_ts"].dt.strftime("%Y-%m-%d %H:%M:%S")
    df["latitude"] = df["latitude"].round(6)
    df["longitude"] = df["longitude"].round(6)
    return df


def main():
    cust = gen_customers()
    sp = gen_service_points()
    apps = gen_applications(cust)
    cust.to_csv("customers_geo.csv", index=False)
    sp.to_csv("service_points.csv", index=False)
    apps.to_csv("loan_applications_geo.csv", index=False)
    print("customers_geo       :", cust.shape)
    print("service_points      :", sp.shape)
    print("loan_applications   :", apps.shape)
    print("default rate        :", round(cust.default_flag.mean(), 3))


if __name__ == "__main__":
    main()
