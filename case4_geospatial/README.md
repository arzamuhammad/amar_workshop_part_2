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

## Prasyarat — PyPI External Access Integration (Notebook on Container Runtime / SPCS)
Notebook ini jalan di **Container Runtime / SPCS** (tidak ada tombol Packages). Paket seperti
**`pydeck`** diinstal via `!pip install`. Bila akun **air-gapped**, pip gagal dengan
`ERROR: Could not find a version that satisfies the requirement pydeck (from versions: none)`.
Solusinya: buat **External Access Integration (EAI) ke PyPI** lalu attach ke notebook.

### Langkah 1 — Buat network rule + EAI (sekali, role ACCOUNTADMIN)
```sql
USE ROLE ACCOUNTADMIN;

CREATE OR REPLACE NETWORK RULE AMAR_WORKSHOP_P2.PUBLIC.PYPI_EGRESS_RULE
  MODE = EGRESS TYPE = HOST_PORT
  VALUE_LIST = ('pypi.org','pypi.python.org','pythonhosted.org','files.pythonhosted.org');

CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION PYPI_ACCESS_INTEGRATION
  ALLOWED_NETWORK_RULES = (AMAR_WORKSHOP_P2.PUBLIC.PYPI_EGRESS_RULE)
  ENABLED = TRUE
  COMMENT = 'Allow pip install from PyPI in Container Runtime notebooks';
```

### Langkah 2 — Attach EAI ke notebook
**Via UI (disarankan):** buka notebook → **⋮ (More) → Notebook settings → External access** →
aktifkan **`PYPI_ACCESS_INTEGRATION`** → **Restart session**.

**Via SQL (bila notebook sudah jadi objek):**
```sql
ALTER NOTEBOOK <db.schema.nama_notebook>
  SET EXTERNAL_ACCESS_INTEGRATIONS = (PYPI_ACCESS_INTEGRATION);
```

### Langkah 3 — Install paket
Jalankan cell `setup`: `!pip install pydeck plotly streamlit` → sekarang berhasil.
(`streamlit` dipakai untuk `st.pydeck_chart`/`st.map`; di Container Runtime belum tentu pra-instal.)

> **Fallback tanpa pip:** bila EAI tidak bisa dipakai, ganti visualisasi pydeck dengan
> `st.map(df)` (kolom `lat`/`lon`) atau `plotly` — komputasi `ST_*`/`H3_*` tetap di SQL.

## Catatan
- Fungsi geospatial **native** (`ST_*`, `H3_*`). Runtime: Container Runtime/SPCS (bukan tombol Packages).
- `LAG` tidak menerima GEOGRAPHY → LAG lat/long lalu `ST_MAKEPOINT`.
- Hindari `st.map(latitude=...)` & param `height` pada `st.pydeck_chart` di runtime Snowflake.

## Jalankan
1. `sql/01_setup_and_load.sql`
2. **Prasyarat di atas:** buat + attach `PYPI_ACCESS_INTEGRATION`, lalu Restart session.
3. Buka notebook → context DB `AMAR_WORKSHOP_P2` schema `GEO` → jalankan cell `setup` (`!pip install pydeck plotly streamlit`) → Run all.
