# Case 1 — Repeat Alarm Forecast

Forecast volume *repeat* harian (nasabah/aplikasi mengulang) untuk *early alarm*.

## Isi
- `data/generate_repeat_data.py` → `repeat_daily_count.csv` (harian total 2019–2026) + `repeat_daily_count_segment.csv` (product × city × repeat_status).
- `sql/01_setup_and_load.sql` → load dari Git Workspace ke `AMAR_WORKSHOP_P2.REPEAT`.
- **Dua varian notebook** (pilih sesuai runtime akun Anda):
  - `notebooks/repeat_alarm_forecast_warehouse.ipynb` — **WAREHOUSE runtime**, paket via **tombol Packages**, **tanpa `pip install`**. ✅ **Aman untuk trial account.**
  - `notebooks/repeat_alarm_forecast_snowflake.ipynb` — **Container Runtime / SPCS**, paket via `!pip install` (butuh **External Access Integration** ke PyPI). ⚠️ **Tidak jalan di trial account.**

  Keduanya isinya sama: EDA → ADF → ACF/PACF → **SARIMAX (statsmodels)** + baseline **Linear Regression** → evaluasi MAE/RMSE → forecast 30 hari → simpan `REPEAT_FORECAST` → **Model Registry** (CustomModel) → **batch inference**.

## Catatan
- **Tanpa `pmdarima`** (tidak ada di Anaconda Snowflake). Order SARIMAX manual `(2,0,2)(1,1,1,7)`, m=7 (musiman mingguan untuk data harian).
- **Batasan trial account:** *external network access* (External Access Integration) **tidak tersedia** di trial
  → `!pip install` dari PyPI selalu gagal. Karena itu pakai varian **warehouse** yang mengambil paket dari
  **Snowflake Anaconda channel** lewat tombol Packages (tidak butuh internet).
- Packages (varian warehouse): `pandas numpy matplotlib plotly scikit-learn statsmodels snowflake-ml-python joblib`.

## Jalankan
1. `sql/01_setup_and_load.sql` (jalankan **per-statement / Run All**, ganti `USER$` dgn username Anda)
2. Pilih notebook:
   - **Trial / warehouse:** buka `repeat_alarm_forecast_warehouse.ipynb` → aktifkan **Packages** (daftar di atas) → Run all.
   - **Non-trial / Container Runtime:** siapkan EAI PyPI → buka `repeat_alarm_forecast_snowflake.ipynb` → jalankan cell `setup` → Run all.
3. Context: DB `AMAR_WORKSHOP_P2`, schema `REPEAT` (sudah di-set otomatis di cell `imports`).
