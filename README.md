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

## Initial Setup (sekali di awal)

Workshop ini memakai pola **Git Workspace** — kode & data ditarik langsung dari GitHub
ke dalam Snowsight Workspace, lalu di-`COPY FILES INTO` ke stage/tabel. Ada **3 langkah**:
buat **API Integration** → buat **Git Workspace** dari repo → jalankan setup DB.

### Langkah 1 — Buat API Integration (Git)
Snowflake butuh **API Integration** agar boleh terhubung ke GitHub. Repo workshop ini
**publik**, jadi tanpa kredensial. Jalankan di worksheet (role `ACCOUNTADMIN`):

```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE API INTEGRATION AMAR_GIT_API
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/arzamuhammad')
  ENABLED = TRUE
  COMMENT = 'Git integration untuk Amar Bank Workshop Part 2';

-- verifikasi
SHOW API INTEGRATIONS LIKE 'AMAR_GIT_API';
```

<details>
<summary><b>Repo privat?</b> (opsional — repo ini publik, jadi bisa dilewati)</summary>

Buat secret berisi **GitHub Personal Access Token (PAT)** lalu izinkan di integration:

```sql
CREATE OR REPLACE SECRET AMAR_GIT_SECRET
  TYPE = password
  USERNAME = 'arzamuhammad'
  PASSWORD = 'ghp_xxxxxxxxxxxxxxxxxxxx';   -- PAT dengan scope 'repo'

CREATE OR REPLACE API INTEGRATION AMAR_GIT_API
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/arzamuhammad')
  ALLOWED_AUTHENTICATION_SECRETS = (AMAR_GIT_SECRET)
  ENABLED = TRUE;
```
</details>

### Langkah 2 — Buat Git Workspace dari repo
**Opsi A — via Snowsight UI (disarankan):**
1. Snowsight → **Projects → Workspaces → `+` (dropdown) → From Git repository**
2. **Repository URL:** `https://github.com/arzamuhammad/amar_workshop_part_2`
3. **API Integration:** pilih `AMAR_GIT_API` (yang dibuat di Langkah 1)
4. **Credentials:** *Public repository* (atau pilih secret `AMAR_GIT_SECRET` bila privat)
5. **Workspace name:** `amar_workshop_part_2` → **Create** (tunggu sinkron)

**Opsi B — via SQL (Git Repository object):**
```sql
USE DATABASE AMAR_WORKSHOP_P2;   -- jalankan Langkah 3 dulu bila DB belum ada
USE SCHEMA PUBLIC;

CREATE OR REPLACE GIT REPOSITORY AMAR_WORKSHOP_REPO
  API_INTEGRATION = AMAR_GIT_API
  ORIGIN = 'https://github.com/arzamuhammad/amar_workshop_part_2.git';
  -- GIT_CREDENTIALS = AMAR_GIT_SECRET   -- hanya untuk repo privat

ALTER GIT REPOSITORY AMAR_WORKSHOP_REPO FETCH;   -- tarik konten terbaru
SHOW GIT BRANCHES IN AMAR_WORKSHOP_REPO;
LS @AMAR_WORKSHOP_REPO/branches/main;             -- lihat file
```

### Langkah 3 — Setup database & schema
```sql
-- dari worksheet, atau: EXECUTE IMMEDIATE FROM @AMAR_WORKSHOP_REPO/branches/main/sql/00_setup_database.sql
USE ROLE ACCOUNTADMIN;
-- lalu jalankan isi sql/00_setup_database.sql (buat AMAR_WORKSHOP_P2 + 4 schema)
```

> **Path `COPY FILES INTO`:** semua case memakai
> `snow://workspace/USER$.PUBLIC."amar_workshop_part_2"/versions/live/`.
> Ganti `USER$` sesuai user Anda (lihat `SELECT CURRENT_USER();`).
> Bila memakai Git Repository object (Opsi B), path alternatifnya
> `@AMAR_WORKSHOP_P2.PUBLIC.AMAR_WORKSHOP_REPO/branches/main/...`.

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
