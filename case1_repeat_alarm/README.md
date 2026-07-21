# Case 1 — Repeat Alarm Forecast

Forecast volume *repeat* harian (nasabah/aplikasi mengulang) untuk *early alarm*.

## Isi
- `data/generate_repeat_data.py` → `repeat_daily_count.csv` (harian total 2019–2026) + `repeat_daily_count_segment.csv` (product × city × repeat_status).
- `sql/01_setup_and_load.sql` → load dari Git Workspace ke `AMAR_WORKSHOP_P2.REPEAT`.
- `notebooks/repeat_alarm_forecast_snowflake.ipynb` → Snowflake Notebook: EDA → ADF → ACF/PACF → **SARIMAX (statsmodels)** + baseline **Linear Regression** → evaluasi MAE/RMSE → forecast 30 hari → simpan `REPEAT_FORECAST`.

## Catatan
- **Tanpa `pmdarima`** (tidak ada di Anaconda Snowflake). Order SARIMAX manual `(2,0,2)(1,1,1,7)`, m=7 (musiman mingguan untuk data harian).
- Packages notebook: `pandas numpy matplotlib plotly scikit-learn statsmodels`.

## Jalankan
1. `sql/01_setup_and_load.sql`
2. Buka notebook → set context (DB `AMAR_WORKSHOP_P2`, schema `REPEAT`) → Run all.
