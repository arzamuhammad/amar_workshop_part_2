/* ============================================================================
   CASE 2 — PAID REJECTION  |  03_semantic_view.sql
   Semantic View untuk Cortex Analyst (self-serve NL query oleh tim bisnis).
   Contoh pertanyaan: "berapa approval rate per kota bulan ini?",
   "alasan reject terbanyak untuk nasabah income <5jt?"
   ============================================================================ */
USE ROLE ACCOUNTADMIN;
USE DATABASE AMAR_WORKSHOP_P2;
USE SCHEMA REJECTION;

CREATE OR REPLACE SEMANTIC VIEW SV_PAID_REJECTION
  TABLES (
    LOANS AS VW_PAID_REJECTION PRIMARY KEY (APP_ID)
      COMMENT = 'Loan application funnel datamart (Paid Rejection)'
  )
  FACTS (
    LOANS.LOAN_AMOUNT AS LOAN_AMOUNT,
    LOANS.PROB_DEFAULT AS PROB_DEFAULT,
    LOANS.FRAUD_SCORE AS FRAUD_SCORE,
    LOANS.PAIDOUT_FLAG AS IS_PAIDOUT,
    LOANS.REJECTED_FLAG AS IS_REJECTED,
    LOANS.ACCEPTED_FLAG AS IS_ACCEPTED
  )
  DIMENSIONS (
    LOANS.APP_ID AS APP_ID,
    LOANS.CITY AS CITY WITH SYNONYMS = ('kota','domisili') COMMENT = 'Kota KTP nasabah',
    LOANS.APP_TYPE AS APP_TYPE WITH SYNONYMS = ('tipe aplikasi','produk'),
    LOANS.FUNNEL_STAGE AS FUNNEL_STAGE COMMENT = 'Tahap funnel terjauh',
    LOANS.REJECT_REASON AS REJECT_REASON WITH SYNONYMS = ('alasan tolak','alasan reject'),
    LOANS.GENDER AS GENDER,
    LOANS.EDUCATION AS EDUCATION,
    LOANS.OCCUPATION AS OCCUPATION,
    LOANS.AGE_BAND AS AGE_BAND,
    LOANS.INCOME_BAND AS INCOME_BAND,
    LOANS.REPEAT_STATUS AS REPEAT_STATUS,
    LOANS.MEDIASOURCE AS MEDIASOURCE,
    LOANS.DECISION_TYPE AS DECISION_TYPE,
    LOANS.CREATED_DATE AS CREATED_DATE,
    LOANS.CREATED_MONTH AS CREATED_MONTH
  )
  METRICS (
    LOANS.TOTAL_APPLICATIONS AS COUNT(APP_ID) COMMENT = 'Jumlah aplikasi',
    LOANS.TOTAL_PAIDOUT AS SUM(IS_PAIDOUT) COMMENT = 'Jumlah aplikasi paid out',
    LOANS.TOTAL_REJECTED AS SUM(IS_REJECTED) COMMENT = 'Jumlah aplikasi ditolak',
    LOANS.APPROVAL_RATE AS SUM(IS_PAIDOUT)/NULLIF(COUNT(APP_ID),0) COMMENT = 'Approval/paid-out rate',
    LOANS.REJECT_RATE AS SUM(IS_REJECTED)/NULLIF(COUNT(APP_ID),0) COMMENT = 'Reject rate',
    LOANS.TOTAL_LOAN_AMOUNT AS SUM(LOAN_AMOUNT) COMMENT = 'Total nilai pinjaman diajukan',
    LOANS.AVG_PROB_DEFAULT AS AVG(PROB_DEFAULT) COMMENT = 'Rata-rata probability of default'
  )
  COMMENT = 'Semantic view untuk Cortex Analyst - Paid Rejection datamart Amar Bank';

-- Uji cepat:
SELECT * FROM SEMANTIC_VIEW(
  SV_PAID_REJECTION DIMENSIONS CITY METRICS TOTAL_APPLICATIONS, APPROVAL_RATE, REJECT_RATE
) ORDER BY TOTAL_APPLICATIONS DESC;

/* Cara pakai (tim bisnis):
   Snowsight -> AI & ML -> Cortex Analyst -> pilih semantic view SV_PAID_REJECTION
   Contoh pertanyaan natural language:
     - "Berapa approval rate per kota?"
     - "Alasan reject terbanyak untuk income band <5jt"
     - "Tren jumlah aplikasi per bulan untuk PDF loan"
     - "Rata-rata probability of default per pekerjaan"
*/
