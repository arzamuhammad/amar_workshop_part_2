# Case 4 — Geospatial Analytics (Digital Bank)

Use case **Location Intelligence & Geo-Fraud** untuk digital bank.

## Isi
- `data/generate_geo_data.py` → `customers_geo.csv` (10k), `service_points.csv` (200 ATM/Cabang/Agen), `loan_applications_geo.csv` (15k, dengan skenario fraud).
- `sql/01_setup_and_load.sql` → load 3 tabel ke `AMAR_WORKSHOP_P2.GEO`.
- `sql/02_geospatial_queries.sql` → referensi query (versi SQL dari notebook).
- `notebooks/geospatial_analysis_snowflake.ipynb` → analisa lengkap + visualisasi **pydeck**.

## Yang dianalisa
- **A. Coverage:** jarak nasabah → titik layanan terdekat (`ST_DISTANCE`), nasabah *underserved* (>5km), coverage per kota, center point (`ST_CENTROID`), H3 risk map.
- **B. Geo-Fraud:** *fraud ring* (cluster titik sama via H3 res 9) & *impossible travel* (>100km dalam <180 menit via `ST_DISTANCE` + `LAG`).
- **Visualisasi:** peta titik A→B (nasabah→layanan) dengan `ScatterplotLayer` + `LineLayer`, H3 `H3HexagonLayer`.

## Catatan
- Fungsi geospatial **native** (`ST_*`, `H3_*`). Packages notebook: `pandas numpy pydeck plotly`.
- `LAG` tidak menerima GEOGRAPHY → LAG lat/long lalu `ST_MAKEPOINT`.
- Hindari `st.map(latitude=...)` & param `height` pada `st.pydeck_chart` di runtime Snowflake.

## Jalankan
1. `sql/01_setup_and_load.sql`
2. Buka notebook → context DB `AMAR_WORKSHOP_P2` schema `GEO` → Run all.
