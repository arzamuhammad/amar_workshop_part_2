# Case 4 — Geospatial Analytics (Digital Bank)

Use case **Location Intelligence & Geo-Fraud** untuk digital bank.

## Isi
- `data/generate_geo_data.py` → `customers_geo.csv` (10k), `service_points.csv` (200 ATM/Cabang/Agen), `loan_applications_geo.csv` (15k, dengan skenario fraud).
- `sql/01_setup_and_load.sql` → load 3 tabel ke `AMAR_WORKSHOP_P2.GEO`.
- `sql/02_geospatial_queries.sql` → referensi query (versi SQL dari notebook).
- `notebooks/geospatial_analysis_snowflake.ipynb` → versi **Container Runtime / SPCS**: paket via `!pip install` (butuh EAI PyPI), peta pakai **plotly `scatter_geo`**.
- `notebooks/geospatial_analysis_warehouse.ipynb` → versi **Warehouse runtime (Streamlit Notebook)**: paket via **tombol Packages** (`pandas numpy pydeck`), peta pakai **pydeck** (`st.pydeck_chart`).

## Yang dianalisa
- **A. Coverage:** jarak nasabah → titik layanan terdekat (`ST_DISTANCE`), nasabah *underserved* (>5km), coverage per kota, center point (`ST_CENTROID`), H3 risk map.
- **B. Geo-Fraud:** *fraud ring* (cluster titik sama via H3 res 9) & *impossible travel* (>100km dalam <180 menit via `ST_DISTANCE` + `LAG`).
- **Visualisasi:** peta titik A→B (nasabah→layanan) & sebaran risiko pakai **plotly `scatter_geo`/`Scattergeo`** (offline, tanpa token).

## Prasyarat — PyPI External Access Integration (Notebook on Container Runtime / SPCS)
Notebook ini jalan di **Container Runtime / SPCS** (tidak ada tombol Packages). Paket seperti
**`plotly`** diinstal via `!pip install`. Bila akun **air-gapped**, pip gagal dengan
`ERROR: Could not find a version that satisfies the requirement ... (from versions: none)`.
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
Jalankan cell `setup`: `!pip install plotly` → sekarang berhasil.

> **Kenapa bukan pydeck?** Snowflake Notebook **memblokir `<script>` di output HTML**, sehingga
> `pydeck.to_html()` (yang menyisipkan JS deck.gl) diblokir; `st.pydeck_chart(...)` juga tidak
> me-render (Container Runtime bukan runtime Streamlit → `missing ScriptRunContext`). Karena itu
> peta memakai **plotly `scatter_geo`** yang didukung native (tanpa `<script>` mentah, tanpa token).

> **Fallback:** komputasi `ST_*`/`H3_*` tetap di SQL; hanya lapisan visualisasi yang pakai plotly,
> jadi mudah diganti chart lain bila perlu.

## Catatan
- Fungsi geospatial **native** (`ST_*`, `H3_*`). Runtime: Container Runtime/SPCS (bukan tombol Packages).
- `LAG` tidak menerima GEOGRAPHY → LAG lat/long lalu `ST_MAKEPOINT`.
- Peta di-render dengan **plotly** (`scatter_geo`), **bukan** pydeck/`st.*` (script HTML diblokir & Streamlit tak jalan di Container Runtime).

## Jalankan
1. `sql/01_setup_and_load.sql`
2. **Pilih versi notebook:**
   - **Warehouse (legacy/Streamlit Notebook)** → buka `geospatial_analysis_warehouse.ipynb`, aktifkan paket via **tombol Packages** (`pandas numpy pydeck`) → Run all. *Tidak perlu EAI.*
   - **Container Runtime / SPCS** → lakukan **Prasyarat EAI** di atas, lalu buka `geospatial_analysis_snowflake.ipynb`, jalankan cell `setup` (`!pip install plotly`) → Run all.
3. Pastikan context DB `AMAR_WORKSHOP_P2` schema `GEO`.
