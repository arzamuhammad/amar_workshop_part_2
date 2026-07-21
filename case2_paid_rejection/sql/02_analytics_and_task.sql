/* ============================================================================
   CASE 2 — PAID REJECTION  |  02_analytics_and_task.sql
   - Curated view (alias kolom -> UPPERCASE bersih, + derived fields)
   - Aggregated mart harian
   - TASK penjadwalan (pengganti scheduled query BigQuery) -- BUKAN Dynamic Table
   ============================================================================ */
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE GEN2_SMALL;
USE DATABASE AMAR_WORKSHOP_P2;
USE SCHEMA REJECTION;

-- 1) CURATED VIEW -----------------------------------------------------------
--    Datamart asli 326 kolom mixed-case. View ini mengambil kolom kunci +
--    membuat derived field (funnel stage, banding umur/income) utk dashboard.
CREATE OR REPLACE VIEW VW_PAID_REJECTION AS
SELECT
    "app_id"                              AS APP_ID,
    "Ref_Num"                             AS REF_NUM,
    "Cust_ID"                             AS CUST_ID,
    "App_Type"                            AS APP_TYPE,
    "App_Status"                          AS APP_STATUS,
    "Loan_Amount"                         AS LOAN_AMOUNT,
    "purpose"                             AS PURPOSE,
    "Created_Date"::DATE                  AS CREATED_DATE,
    DATE_TRUNC('month', "Created_Date")   AS CREATED_MONTH,
    -- funnel stage terjauh
    CASE
        WHEN "Paid_Out_Cnt" = 1 THEN 'PaidOut'
        WHEN "Printed_Cnt"  = 1 THEN 'Printed'
        WHEN "Acc_Cnt"      = 1 THEN 'Accepted'
        WHEN "Rej_Cust_Cnt" = 1 THEN 'Rejected'
        WHEN "Dropoff_Cnt"  = 1 THEN 'Dropoff'
        ELSE 'Pending'
    END                                   AS FUNNEL_STAGE,
    "Paid_Out_Cnt"                        AS IS_PAIDOUT,
    "Acc_Cnt"                             AS IS_ACCEPTED,
    "Rej_Cust_Cnt"                        AS IS_REJECTED,
    "reject_reason"                       AS REJECT_REASON,
    "reject_sub_reason"                   AS REJECT_SUB_REASON,
    "decision_type"                       AS DECISION_TYPE,
    "selected_probability_of_default"     AS PROB_DEFAULT,
    "fraud_score"                         AS FRAUD_SCORE,
    "zero_payer_score"                    AS ZERO_PAYER_SCORE,
    "score_model"                         AS SCORE_MODEL,
    "Score_Type"                          AS SCORE_TYPE,
    -- demografi
    "gender"                              AS GENDER,
    "religion"                            AS RELIGION,
    "education"                           AS EDUCATION,
    "marital_status"                      AS MARITAL_STATUS,
    "Occupation"                          AS OCCUPATION,
    "cust_age"                            AS AGE,
    CASE WHEN "cust_age" < 25 THEN '<25'
         WHEN "cust_age" < 35 THEN '25-34'
         WHEN "cust_age" < 45 THEN '35-44'
         WHEN "cust_age" < 55 THEN '45-54' ELSE '55+' END AS AGE_BAND,
    "income"                              AS INCOME,
    CASE WHEN "income" < 5e6  THEN '<5jt'
         WHEN "income" < 10e6 THEN '5-10jt'
         WHEN "income" < 20e6 THEN '10-20jt'
         ELSE '20jt+' END                 AS INCOME_BAND,
    "num_of_dependants"                   AS NUM_DEPENDANTS,
    "City_KTP"                            AS CITY,
    "area_tag"                            AS AREA,
    "zip_code_ktp_last"                   AS ZIP_CODE,
    "Mediasource"                         AS MEDIASOURCE,
    "repeat_status"                       AS REPEAT_STATUS,
    "period"                              AS TENOR,
    "interest"                            AS INTEREST,
    "current_overdue"                     AS CURRENT_OVERDUE,
    -- geo (nyambung Case 4)
    "latitude_at_submit"                  AS LATITUDE,
    "longitude_at_submit"                 AS LONGITUDE,
    "suspicious_lat_long"                 AS SUSPICIOUS_LATLONG
FROM PAID_REJECTION_DATAMART;

-- 2) AGGREGATED MART (di-refresh oleh TASK) --------------------------------
CREATE OR REPLACE TABLE MART_REJECTION_DAILY (
    CREATED_DATE   DATE,
    CITY           STRING,
    APP_TYPE       STRING,
    N_CREATED      NUMBER,
    N_ACCEPTED     NUMBER,
    N_PAIDOUT      NUMBER,
    N_REJECTED     NUMBER,
    AMT_CREATED    FLOAT,
    AMT_PAIDOUT    FLOAT,
    APPROVAL_RATE  FLOAT,
    REJECT_RATE    FLOAT,
    REFRESHED_AT   TIMESTAMP_NTZ
);

-- Stored procedure yang membangun ulang mart (logika "scheduled query")
CREATE OR REPLACE PROCEDURE SP_REFRESH_REJECTION_MART()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
    CREATE OR REPLACE TABLE MART_REJECTION_DAILY AS
    SELECT
        CREATED_DATE,
        CITY,
        APP_TYPE,
        COUNT(*)                                             AS N_CREATED,
        SUM(IS_ACCEPTED)                                     AS N_ACCEPTED,
        SUM(IS_PAIDOUT)                                      AS N_PAIDOUT,
        SUM(IS_REJECTED)                                     AS N_REJECTED,
        SUM(LOAN_AMOUNT)                                     AS AMT_CREATED,
        SUM(IFF(IS_PAIDOUT=1, LOAN_AMOUNT, 0))               AS AMT_PAIDOUT,
        ROUND(SUM(IS_PAIDOUT)/NULLIF(COUNT(*),0), 4)         AS APPROVAL_RATE,
        ROUND(SUM(IS_REJECTED)/NULLIF(COUNT(*),0), 4)        AS REJECT_RATE,
        CURRENT_TIMESTAMP()                                  AS REFRESHED_AT
    FROM VW_PAID_REJECTION
    GROUP BY CREATED_DATE, CITY, APP_TYPE;
    RETURN 'MART_REJECTION_DAILY refreshed';
END;
$$;

CALL SP_REFRESH_REJECTION_MART();   -- jalankan sekali untuk inisialisasi

-- 3) TASK penjadwalan (pengganti scheduled BigQuery) -----------------------
--    Refresh mart tiap hari 01:00 Asia/Jakarta. Aktifkan dengan RESUME.
CREATE OR REPLACE TASK TSK_REFRESH_REJECTION_MART
    WAREHOUSE = GEN2_SMALL
    SCHEDULE  = 'USING CRON 0 1 * * * Asia/Jakarta'
    COMMENT   = 'Refresh datamart Paid Rejection harian (pengganti scheduled query BigQuery)'
AS
    CALL SP_REFRESH_REJECTION_MART();

-- ALTER TASK TSK_REFRESH_REJECTION_MART RESUME;   -- uncomment utk mengaktifkan
-- EXECUTE TASK TSK_REFRESH_REJECTION_MART;         -- untuk trigger manual (uji)

/* ALTERNATIF: jadwalkan lewat Snowflake NOTEBOOK (menu "Schedule" di notebook)
   bila ingin logika Python. Task di atas = versi SQL murni. */

SELECT * FROM MART_REJECTION_DAILY ORDER BY CREATED_DATE DESC LIMIT 10;
