/* ============================================================================
   CASE 1 — REPEAT ALARM  |  01_setup_and_load.sql
   Amar Bank Workshop Part 2
   Pola load: Git Workspace -> COPY FILES INTO stage -> COPY INTO table
   (mengikuti pattern flood-resilience)
   ----------------------------------------------------------------------------
   PRA-SYARAT:
     - Sudah membuat GIT WORKSPACE dari repo github.com/arzamuhammad/amar_workshop_part_2
     - Nama workspace di Snowsight = "amar_workshop_part_2"
       (kalau beda, sesuaikan path snow://workspace/... di bawah)
   ----------------------------------------------------------------------------
   CARA MENJALANKAN (PENTING):
     File ini berisi BANYAK statement. Jalankan PER-STATEMENT atau "Run All" —
     JANGAN dikirim sebagai satu panggilan API.
       - Snowsight Worksheet/Workspace : taruh kursor di 1 statement lalu
         Cmd/Ctrl+Enter, atau klik "Run All" (kanan atas).
       - Snowflake CLI                 : snow sql -f 01_setup_and_load.sql
       - SQL API / Python connector    : loop per-statement, atau set
         ALTER SESSION SET MULTI_STATEMENT_COUNT = 0;
     Kalau muncul error "Multiple SQL statements in a single API call are not
     supported", artinya seluruh file terkirim sebagai satu call -> pakai salah
     satu cara di atas.
   ----------------------------------------------------------------------------
   GANTI PLACEHOLDER:
     USER$  -> username Snowflake Anda (cek: SELECT CURRENT_USER();)
               contoh: ARDIYANMUHAMMAD
   ============================================================================ */

USE ROLE ACCOUNTADMIN;
USE WAREHOUSE GEN2_SMALL;
USE DATABASE AMAR_WORKSHOP_P2;
USE SCHEMA REPEAT;

-- 1) File format & stage internal ------------------------------------------
CREATE OR REPLACE FILE FORMAT CSV_FORMAT
  TYPE = CSV
  PARSE_HEADER = TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

CREATE OR REPLACE STAGE REPEAT_DATA_STAGE
  DIRECTORY = (ENABLE = TRUE)
  ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE');

-- 2) Copy CSV dari Git Workspace ke stage -----------------------------------
--    PENTING: ganti USER$ dengan username Anda (mis. ARDIYANMUHAMMAD).
--    Path 'versions/live/' = versi workspace yang sedang aktif.
--    Jalankan statement ini SENDIRI (jangan bersama statement lain).
COPY FILES INTO @REPEAT_DATA_STAGE/
FROM 'snow://workspace/USER$.PUBLIC."amar_workshop_part_2"/versions/live/'
FILES = (
  'case1_repeat_alarm/data/repeat_daily_count.csv',
  'case1_repeat_alarm/data/repeat_daily_count_segment.csv'
);

ALTER STAGE REPEAT_DATA_STAGE REFRESH;
LS @REPEAT_DATA_STAGE;

-- 3) Tabel target -----------------------------------------------------------
CREATE OR REPLACE TABLE REPEAT_DAILY_COUNT (
  CREATED_DATE  DATE,
  REPEAT_COUNT  NUMBER
);

CREATE OR REPLACE TABLE REPEAT_DAILY_COUNT_SEGMENT (
  CREATED_DATE   DATE,
  PRODUCT        STRING,
  CITY           STRING,
  REPEAT_STATUS  STRING,
  REPEAT_COUNT   NUMBER
);

-- 4) Load (MATCH_BY_COLUMN_NAME karena PARSE_HEADER = TRUE) ------------------
COPY INTO REPEAT_DAILY_COUNT
FROM @REPEAT_DATA_STAGE/case1_repeat_alarm/data/repeat_daily_count.csv
FILE_FORMAT = CSV_FORMAT
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'CONTINUE';

COPY INTO REPEAT_DAILY_COUNT_SEGMENT
FROM @REPEAT_DATA_STAGE/case1_repeat_alarm/data/repeat_daily_count_segment.csv
FILE_FORMAT = CSV_FORMAT
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
ON_ERROR = 'CONTINUE';

-- 5) Validasi ---------------------------------------------------------------
SELECT 'total'   AS tbl, COUNT(*) AS n, MIN(CREATED_DATE) AS d_min, MAX(CREATED_DATE) AS d_max FROM REPEAT_DAILY_COUNT
UNION ALL
SELECT 'segment' AS tbl, COUNT(*) AS n, MIN(CREATED_DATE) AS d_min, MAX(CREATED_DATE) AS d_max FROM REPEAT_DAILY_COUNT_SEGMENT;

/* ----------------------------------------------------------------------------
   ALTERNATIF (tanpa file): generate data langsung via SQL.
   Berguna kalau tidak ingin membawa CSV besar di repo. Contoh series harian
   dengan trend + weekly + yearly seasonality:

   CREATE OR REPLACE TABLE REPEAT_DAILY_COUNT AS
   WITH d AS (
     SELECT DATEADD('day', SEQ4(), DATE '2019-01-01') AS created_date
     FROM TABLE(GENERATOR(ROWCOUNT => 2769))
   )
   SELECT created_date,
          GREATEST(20, ROUND(
             (1300 + 1.1 * DATEDIFF('day','2019-01-01',created_date))          -- trend
             * (1 + 0.18*SIN(2*PI()*DAYOFYEAR(created_date)/365.25))            -- yearly
             * (CASE WHEN DAYOFWEEK(created_date) IN (0,6) THEN 0.62 ELSE 1 END)-- weekly
             * (1 + UNIFORM(-0.12, 0.12, RANDOM()))                            -- noise
          ))::NUMBER AS repeat_count
   FROM d;
   ---------------------------------------------------------------------------- */
