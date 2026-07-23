# Case 2 — Paid Rejection Datamart (Open Table)

Datamart loan-origination funnel **326 kolom** (Created→Accepted→Printed→PaidOut/Rejected + demografi + scoring + geo). Menggantikan scheduled BigQuery, dan menyediakan self-serve analytics + dashboard.

## Isi
- `data/generate_datamart.py` → `paid_rejection_datamart.csv.gz` (100k aplikasi, 12 bulan, **semua 326 kolom**).
- `sql/01_setup_and_load.sql` → DDL 326 kolom + load dari Git Workspace.
- `sql/02_analytics_and_task.sql` → `VW_PAID_REJECTION` (curated, alias bersih + derived) + `MART_REJECTION_DAILY` + **Task** `TSK_REFRESH_REJECTION_MART` (cron harian, pengganti scheduled query).
- `sql/03_semantic_view.sql` → `SV_PAID_REJECTION` untuk **Cortex Analyst** (self-serve NL).
- `streamlit/` → dashboard funnel / reject / demografi / geo. Dibangun via **Streamlit in Workspaces**: buka `streamlit_app.py` di Git Workspace → **Run** (preview) → **Deploy** jadi `PAID_REJECTION_DASHBOARD` (schema REJECTION). Dependency di `streamlit/pyproject.toml`. App jalan di **compute pool** (container runtime).

## Refresh (BUKAN Dynamic Table)
`ALTER TASK TSK_REFRESH_REJECTION_MART RESUME;` untuk aktifkan jadwal, atau
`EXECUTE TASK TSK_REFRESH_REJECTION_MART;` untuk trigger manual. Alternatif: jadwalkan via Snowflake Notebook.

## Cortex Analyst
Snowsight → AI & ML → Cortex Analyst → pilih `SV_PAID_REJECTION`. Contoh:
"approval rate per kota", "alasan reject terbanyak income <5jt", "tren aplikasi per bulan".
