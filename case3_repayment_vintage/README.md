# Case 3 — Repayment Vintage: Looker → Google Sheet (Snowflake)

Menggantikan alur lama **BigQuery → Looker "Look" → Google Sheet (Apps Script)** dengan
**Snowflake → (SQL API / Streamlit)**.

## Struktur data
- `LOAN_REPAYMENT_VINTAGE` — tabel wide 159 kolom (persis file Looker `bquxjob_*.csv`): `month_0..24` × {payment, crm, bank, cumulative, cumulative_crm, cumulative_bank}.
- `VW_REPAYMENT_LONG` — hasil **unpivot** wide→long (`ref_num, month_index, payment, cumulative, ...`). *Teaching point:* format long jauh lebih mudah dianalisa/divisualisasi.
- `VW_PAYBACK_CURVE` — agregat payback rate per cohort (bulan disburse) × bulan-ke-N × tipe. Ini "Look" utama.

## Opsi A — Google Sheet via Apps Script + Snowflake SQL API
Folder `appscript/Code.gs`. Alur: Apps Script memanggil **Snowflake SQL API** (`/api/v2/statements`) dengan **PAT** (Programmatic Access Token), menulis hasil ke Sheet, lalu **formula tetap diolah di Sheet** (persis pengganti Looker API lama).

Langkah:
1. Buat PAT di Snowsight (Users & Roles → Generate Token).
2. Apps Script → Project Settings → **Script Properties**:
   - `SNOWFLAKE_ACCOUNT_URL` = `https://<org>-<account>.snowflakecomputing.com`
   - `SNOWFLAKE_PAT` = token
   - `SNOWFLAKE_WAREHOUSE` = `GEN2_SMALL`
   - `SNOWFLAKE_ROLE` = `ACCOUNTADMIN`
3. Refresh Sheet → menu **Snowflake** → *Refresh Payback Curve*.
4. Atau pakai custom formula di cell: `=SNOWQUERY("SELECT MONTH_INDEX, ROUND(AVG(PAYBACK_RATE)*100,2) FROM AMAR_WORKSHOP_P2.REPAYMENT.VW_PAYBACK_CURVE GROUP BY 1 ORDER BY 1")`

> Jika kolom lama diproses dengan formula tertentu di Apps Script, salin logikanya ke fungsi baru (mis. `SNOWQUERY` + kolom turunan di sheet). Hasil akhir tetap sama, sumber pindah dari Looker ke Snowflake.

## Opsi B — Streamlit in Snowflake
`streamlit/streamlit_app.py` → dashboard payback curve, CRM vs Bank, cohort heatmap.
Sudah dideploy sebagai **`PAYBACK_CURVE_DASHBOARD`** (schema REPAYMENT).

## Urutan menjalankan
1. `sql/01_setup_and_load.sql` (load dari Git Workspace) — atau data sudah di-load.
2. `sql/02_views.sql` (unpivot + payback curve).
3. Opsi A: setup `appscript/Code.gs`. Opsi B: buka Streamlit `PAYBACK_CURVE_DASHBOARD`.
