# Amar Bank — Snowflake Workshop Part 2

Hands-on lab & workshop mencakup **4 case** yang dibangun di atas Snowflake, mengikuti pola
**Git Workspace + Snowflake Notebook + `COPY FILES INTO`** (seperti `qureshifawad/flood-resilience`).

Database: **`AMAR_WORKSHOP_P2`** (schema per-case: `REPEAT`, `REJECTION`, `REPAYMENT`, `GEO`).

| Case | Topik | Snowflake features |
|------|-------|--------------------|
| 1 | **Repeat Alarm Forecast** | Snowflake Notebook, statsmodels **SARIMAX** (tanpa pmdarima), Linear Regression, forecast → tabel |
| 2 | **Paid Rejection Datamart** | Open table 326 kolom, **Task** scheduler (bukan Dynamic Table), **Semantic View → Cortex Analyst**, **Streamlit** |
| 3 | **Repayment Vintage** (Looker→Sheet) | Unpivot wide→long, **Google Apps Script + SQL API**, **Streamlit** payback curve |
| 4 | **Geospatial** (Digital Bank) | `ST_MAKEPOINT/ST_DISTANCE/ST_CENTROID`, **H3**, coverage + geo-fraud, **pydeck** |

## Struktur repo
```
amar_workshop_part_2/
├── case1_repeat_alarm/      data/ (generator + CSV)  notebooks/  sql/
├── case2_paid_rejection/    data/ (326-col gz)       sql/        streamlit/
├── case3_repayment_vintage/ data/ (vintage gz)       sql/  streamlit/  appscript/
└── case4_geospatial/        data/ (geo CSV)          notebooks/  sql/
```

## Prasyarat — Buat Git Workspace (sekali)
Ikuti pola flood-resilience:
1. Snowsight → **Projects → Workspaces → `+` → Git Workspace**
2. Repository URL: `https://github.com/arzamuhammad/amar_workshop_part_2`
3. **API Integration** baru: nama KAPITAL (mis. `AMAR_GIT`), allowed domain `github.com`
4. Workspace name: `amar_workshop_part_2` → **Create** (tunggu sinkron)
5. Jalankan `sql/00_setup_database.sql` (buat DB + schema) sekali.

> Semua `COPY FILES INTO` memakai path `snow://workspace/USER$.PUBLIC."amar_workshop_part_2"/versions/live/`.
> Ganti `USER$` bila perlu sesuai user Anda.

## Alur tiap case
- **Case 1:** `sql/01_setup_and_load.sql` → buka `notebooks/repeat_alarm_forecast_snowflake.ipynb` → Run all.
- **Case 2:** `sql/01_setup_and_load.sql` → `02_analytics_and_task.sql` → `03_semantic_view.sql` → deploy `streamlit/`. Cortex Analyst: pilih `SV_PAID_REJECTION`.
- **Case 3:** `sql/01_setup_and_load.sql` → `02_views.sql` → `streamlit/` (Opsi B) atau `appscript/Code.gs` (Opsi A). Lihat `case3.../README.md`.
- **Case 4:** `sql/01_setup_and_load.sql` → buka `notebooks/geospatial_analysis_snowflake.ipynb` → Run all. Referensi SQL: `sql/02_geospatial_queries.sql`.

## Catatan teknis penting
- **Case 1:** `pmdarima.auto_arima` TIDAK ada di Anaconda Snowflake → dipakai **statsmodels SARIMAX** dengan order manual `(2,0,2)(1,1,1,7)` (m=7 = musiman mingguan untuk data harian).
- **Case 2:** refresh datamart pakai **Task** `TSK_REFRESH_REJECTION_MART` (cron harian) — pengganti scheduled query BigQuery. Bisa juga dijadwalkan lewat Snowflake Notebook.
- **Case 3:** file wide `month_0..24`; di Snowflake di-unpivot ke long (`VW_REPAYMENT_LONG`) untuk kemudahan analisa.
- **Case 4:** semua komputasi jarak pakai fungsi `ST_*`/`H3_*` native; peta pakai `pydeck` (hindari `st.map(latitude=...)` & param `height` pada `st.pydeck_chart`).

## Data
Semua data **sintetis** (numpy/pandas, tanpa PII asli). Generator ada di tiap `data/generate_*.py`.
File besar dikompresi `.csv.gz` agar muat di GitHub.

---
Amar Bank Workshop Part 2 · dibangun dengan Cortex Code.
