# Case 2 — AI BI Dashboard (Cowork Dashboards 2.0) via CoCo prompting

Dashboard **kedua** untuk Paid Rejection (selain Streamlit in Workspaces): **AI BI Dashboard**
di **Snowflake Cowork (Dashboards 2.0 / Artifacts 2.0)**, dibangun **konversasional lewat CoCo**
di Snowsight Workspaces — bukan `.dash` yang ditulis manual.

- **Sumber data:** semantic view `AMAR_WORKSHOP_P2.REJECTION.SV_PAID_REJECTION`
  (metrics: `TOTAL_APPLICATIONS`, `APPROVAL_RATE`, `REJECT_RATE`, `TOTAL_LOAN_AMOUNT`,
  `AVG_PROB_DEFAULT`; dimensions: `CITY`, `APP_TYPE`, `FUNNEL_STAGE`, `REJECT_REASON`,
  `AGE_BAND`, `INCOME_BAND`, `EDUCATION`, `OCCUPATION`, `REPEAT_STATUS`, `CREATED_MONTH`, ...).
- **Data:** 100.000 aplikasi, Agu 2025 → Jul 2026, 8 kota, approval ~41.9%.

> ⚠️ **Private preview** — pastikan akun ter-enroll Cowork Dashboards 2.0.
> **Peta geospasial belum didukung** di PrPr → tab "Geo" dari Streamlit diganti bar/heatmap per kota.

---

## Langkah 0 — Mulai
Snowsight → **Workspaces → Create → Dashboard** (atau ketik `/dashboard` di CoCo). Tempel prompt berurutan.

## Langkah 1 — Prompt master (buat seluruh dashboard)

```text
Build a dashboard called "Amar Bank — Paid Rejection Analytics" using the semantic
view AMAR_WORKSHOP_P2.REJECTION.SV_PAID_REJECTION as the data source.

Top row: five scorecard/KPI tiles, side by side:
1. Total Applications  (metric TOTAL_APPLICATIONS)
2. Approval Rate       (metric APPROVAL_RATE, shown as %)
3. Reject Rate         (metric REJECT_RATE, shown as %)
4. Total Loan Amount   (metric TOTAL_LOAN_AMOUNT, formatted in billions "Rp x.x M")
5. Avg Probability of Default (metric AVG_PROB_DEFAULT, 3 decimals)

Second row (two tiles):
- A horizontal bar chart "Funnel Konversi" = TOTAL_APPLICATIONS by dimension
  FUNNEL_STAGE, ordered Pending, Dropoff, Rejected, Accepted, Printed, PaidOut.
- A line chart "Tren Aplikasi per Bulan" = TOTAL_APPLICATIONS and TOTAL_PAIDOUT
  by CREATED_MONTH, two lines.

Third row (two tiles):
- A horizontal bar "Alasan Penolakan (Top)" = TOTAL_REJECTED by REJECT_REASON,
  sorted descending, top 10.
- A bar "Reject Rate per Kota" = REJECT_RATE by CITY, sorted descending, as %.

Fourth row (three tiles):
- A donut chart "Pendidikan" = TOTAL_APPLICATIONS by EDUCATION.
- A bar "Distribusi Umur" = TOTAL_APPLICATIONS by AGE_BAND.
- A bar "Income Band" = TOTAL_APPLICATIONS by INCOME_BAND.

Fifth row (full width):
- A heatmap "Approval Rate: Income Band x Umur" with INCOME_BAND on rows,
  AGE_BAND on columns, colored by APPROVAL_RATE.

Use the Snowflake brand palette (deep blue #11567F and light blue #29B5E8).
```

## Langkah 2 — Filter dashboard-level

```text
Add four dashboard filters that connect to all relevant tiles:
1. "city"          - multi-select on dimension CITY
2. "app_type"      - multi-select on dimension APP_TYPE
3. "created_date"  - date range on dimension CREATED_DATE
4. "repeat_status" - multi-select on dimension REPEAT_STATUS
Wire them into every tile's WHERE clause using the {{ filter('...') }} placeholders.
```

## Langkah 3 — Iterasi / perapihan (opsional)

```text
- Make the "Tren Aplikasi per Bulan" tile full width.
- On "Reject Rate per Kota", add a red reference line at the overall average reject rate.
- Format all rate tiles as percentages with one decimal.
- On the approval-rate heatmap, show the value labels inside each cell.
- Put the five KPI scorecards in a single top row of equal width.
```

Tile berbasis view langsung (kolom yang tak ada di semantic view), mis. histogram PD:
```text
Add a histogram of PROB_DEFAULT using table AMAR_WORKSHOP_P2.REJECTION.VW_PAID_REJECTION, 40 bins.
```

## Langkah 4 — Deploy ke Cowork

Privilege (jalankan sekali di worksheet):
```sql
-- Wajib untuk deploy (default sudah ke PUBLIC). Contoh mengkurasi:
GRANT MANAGE ARTIFACT PUBLICATION TO ROLE ACCOUNTADMIN;
```
Prompt CoCo:
```text
Deploy this dashboard to Cowork.
Location: database AMAR_WORKSHOP_P2, schema REJECTION.
Share it with role ACCOUNTADMIN (add a business role if needed).
```
Di dialog **Deploy**: cek App title, Location `AMAR_WORKSHOP_P2.REJECTION`, Warehouse `GEN2_SMALL`, role penerima.

> ⚠️ **Caller's rights**: tiap viewer menjalankan query dgn privilege-nya sendiri. Pastikan role penerima
> punya `SELECT` ke `SV_PAID_REJECTION` / `VW_PAID_REJECTION` / `PAID_REJECTION_DATAMART`, atau tile kosong.

## Langkah 5 — Konsumsi (tim bisnis)
Cowork → **Shared with me** → buka dashboard → terapkan filter → tanya follow-up NL pada tile,
mis. *"kenapa reject rate Surabaya paling tinggi?"* atau *"pecah funnel ini per repeat_status."*

---

Semua tile sudah dicocokkan dgn metrics/dimensions `SV_PAID_REJECTION`, jadi CoCo bisa langsung
generate SQL-nya. Dashboard ini pelengkap (bukan pengganti) Streamlit `PAID_REJECTION_DASHBOARD`.
