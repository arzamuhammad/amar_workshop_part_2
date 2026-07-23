# Case 3 — Repayment Vintage / Payback Curve (Looker → Google Sheet → Snowflake)

## 1. Apa yang dikerjakan case ini?
**Vintage analysis** = menganalisa performa pelunasan pinjaman **berdasarkan bulan pencairan (cohort)**.
Pertanyaan bisnis: *"Dari pinjaman yang cair bulan X, berapa % pokok yang sudah terbayar setelah
N bulan berjalan?"* Kurva jawabannya disebut **payback curve** — indikator kualitas kredit & collection.

**Alur lama (yang digantikan):**
```
BigQuery  →  Looker "Look" (query tersimpan)  →  Google Sheet (Apps Script tarik Looker API)  →  formula di Sheet
```
**Alur baru (case ini):**
```
Snowflake (tabel + view)  →  { Streamlit in Workspaces  ATAU  Google Sheet via Snowflake SQL API }
```
Sumber pindah dari Looker/BigQuery ke Snowflake; logika "Look" jadi **SQL View**.

## 2. Model data
### Tabel sumber (WIDE) — `LOAN_REPAYMENT_VINTAGE` (159 kolom)
Persis bentuk file ekspor Looker. 1 baris = 1 pinjaman. Selain kolom identitas
(`REF_NUM`, `APP_ID`, `LOAN_AMOUNT`, `LOAN_PAID_OUT_DATE`, `APP_TYPE`, `RESTRUCT_STATUS`, `SCORE_MODEL`, …),
ada **25 blok bulan** `MONTH_0..MONTH_24`, tiap bulan punya **6 kolom**:

| Sufiks kolom | Arti |
|---|---|
| `MONTH_n_PAYMENT` | pembayaran di bulan-ke-n |
| `MONTH_n_PAYMENT_CRM` | versi catatan **CRM** |
| `MONTH_n_PAYMENT_BANK` | versi catatan **Bank** |
| `MONTH_n_PAYMENT_CUMULATIVE` | pembayaran **kumulatif** s/d bulan-ke-n |
| `MONTH_n_PAYMENT_CUMULATIVE_CRM` | kumulatif versi CRM |
| `MONTH_n_PAYMENT_CUMULATIVE_BANK` | kumulatif versi Bank |

> Format **wide** ini susah dianalisa (25×6 = 150 kolom angka). Karena itu di Snowflake kita ubah ke **long**.

### View 1 (LONG) — `VW_REPAYMENT_LONG`
**Unpivot** `MONTH_0..24` menjadi baris. 1 baris = 1 pinjaman × 1 bulan-ke-n.
Kolom hasil: `REF_NUM, APP_ID, LOAN_AMOUNT, LOAN_PAID_OUT_DATE, APP_TYPE, …, MONTH_INDEX (0..24),
PAYMENT, PAYMENT_CRM, PAYMENT_BANK, CUMULATIVE, CUMULATIVE_CRM, CUMULATIVE_BANK`.
*Teaching point:* format long = 1 kolom nilai + 1 kolom indeks → jauh lebih mudah di-`GROUP BY`/plot.

### View 2 (AGREGAT / "Look") — `VW_PAYBACK_CURVE`
Inti analisa. Payback rate per **cohort** (bulan pencairan) × `APP_TYPE` × `MONTH_INDEX`:
```
PAYBACK_RATE = SUM(CUMULATIVE) / SUM(LOAN_AMOUNT)     -- % pokok terbayar
```
Kolom: `COHORT_MONTH, APP_TYPE, MONTH_INDEX, N_LOANS, TOTAL_PRINCIPAL, TOTAL_PAID, PAYBACK_RATE`.

## 3. Isi folder
```
case3_repayment_vintage/
├── data/generate_repayment.py       generator data sintetis
├── data/repayment_vintage.csv.gz    dataset (wide, 159 kolom)
├── sql/01_setup_and_load.sql        DDL wide + load dari Git Workspace
├── sql/02_views.sql                 VW_REPAYMENT_LONG + VW_PAYBACK_CURVE
├── streamlit/streamlit_app.py       Opsi B: dashboard (Streamlit in Workspaces)
├── streamlit/pyproject.toml         dependency app
└── appscript/Code.gs                Opsi A: Google Sheet via Snowflake SQL API
```

## 4. Urutan menjalankan (WAJIB berurutan)
> Jalankan SQL **per-statement / Run All** (jangan kirim seluruh file sebagai 1 API call).

**Langkah 1 — Load data** → `sql/01_setup_and_load.sql`
- Buat file format + stage, `COPY FILES` dari Git Workspace, buat tabel wide, `COPY INTO`.
- ⚠️ Ganti `USER$` di path `snow://workspace/USER$...` dengan username Anda (`SELECT CURRENT_USER();`).
- Validasi: query terakhir menampilkan `n_rows` & `avg_amt`.

**Langkah 2 — Buat view** → `sql/02_views.sql`
- Membuat `VW_REPAYMENT_LONG` (unpivot) dan `VW_PAYBACK_CURVE` (payback rate).
- Validasi: query terakhir menampilkan `avg_payback` per `MONTH_INDEX` (harusnya naik 0→24).

**Langkah 3 — Pilih cara konsumsi (A dan/atau B):**

### Opsi A — Google Sheet via Snowflake SQL API (pengganti persis Looker→Sheet)
`appscript/Code.gs` memanggil **Snowflake SQL API** (`POST /api/v2/statements`) pakai **PAT**
(Programmatic Access Token), menulis hasil ke Sheet; **formula tetap diolah di Sheet**.

1. **Buat PAT** di Snowsight: *Admin → Users & Roles → pilih user → Generate Token*.
2. Google Sheet → **Extensions → Apps Script**, tempel isi `Code.gs`.
3. Apps Script → **Project Settings → Script Properties** (JANGAN hardcode token):
   - `SNOWFLAKE_ACCOUNT_URL` = `https://<orgname>-<account>.snowflakecomputing.com`
   - `SNOWFLAKE_PAT` = token PAT
   - `SNOWFLAKE_WAREHOUSE` = `GEN2_SMALL`
   - `SNOWFLAKE_ROLE` = `ACCOUNTADMIN`
4. Simpan → refresh Sheet → muncul menu **Snowflake**:
   - **Refresh Payback Curve** → tulis agregat `VW_PAYBACK_CURVE` ke sheet `PaybackCurve`.
   - **Refresh Vintage Raw** → tulis long data (≤ bulan 12) ke sheet `VintageRaw`.
5. Atau custom formula di cell (hasil spill sebagai array):
   ```
   =SNOWQUERY("SELECT MONTH_INDEX, ROUND(AVG(PAYBACK_RATE)*100,2) FROM AMAR_WORKSHOP_P2.REPAYMENT.VW_PAYBACK_CURVE GROUP BY 1 ORDER BY 1")
   ```
> Kalau dulu ada formula khusus di Apps Script (dari Looker), salin logikanya ke `SNOWQUERY` + kolom
> turunan di sheet. Hasil akhir sama, sumber pindah Looker → Snowflake.

### Opsi B — Streamlit in Snowflake (di Workspaces)
`streamlit/streamlit_app.py` = dashboard payback curve, CRM vs Bank, cohort heatmap. Tiga tab:
- **Payback Curve** — kurva pelunasan kumulatif per `APP_TYPE`.
- **CRM vs Bank** — gap kolektibilitas antara catatan CRM & Bank (bahan rekonsiliasi).
- **Cohort Heatmap** — payback % per cohort × bulan-ke-n (vintage klasik).

Langkah (Streamlit in Workspaces — bukan classic SiS):
1. Di Git Workspace `amar_workshop_part_2`, buka `case3_repayment_vintage/streamlit/streamlit_app.py`.
2. **Run** (`Cmd/Ctrl+Enter`) untuk preview *development app* (privat). Dependency di `pyproject.toml`.
3. **Deploy** → Location DB=`AMAR_WORKSHOP_P2` schema=`REPAYMENT`, Execution = compute pool + warehouse
   `GEN2_SMALL`, Sharing = role penerima → **Deploy** (objek `PAYBACK_CURVE_DASHBOARD`).
- Prasyarat: **USAGE compute pool** + default warehouse (app jalan di *container runtime*),
  **CREATE STREAMLIT** pada schema untuk deploy. Detail: skill `streamlit-in-workspaces`.

## 5. Glosarium singkat
- **Cohort / vintage** = grup pinjaman berdasarkan bulan pencairan (`LOAN_PAID_OUT_DATE`).
- **MONTH_INDEX** = umur pinjaman (bulan-ke-0 = bulan cair, dst).
- **Payback rate** = `kumulatif terbayar / pokok`; makin cepat naik ke 100% makin sehat.
- **CRM vs Bank** = dua sumber pencatatan pembayaran; selisihnya perlu direkonsiliasi.

## 6. Data
Sintetis (lihat `data/generate_repayment.py`), tanpa PII asli. Disimpan `.csv.gz` agar muat di GitHub.
