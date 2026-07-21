/* ============================================================================
   00_setup_database.sql — Amar Bank Workshop Part 2
   Jalankan sekali sebelum case manapun.
   ============================================================================ */
USE ROLE ACCOUNTADMIN;
CREATE DATABASE IF NOT EXISTS AMAR_WORKSHOP_P2;
CREATE SCHEMA IF NOT EXISTS AMAR_WORKSHOP_P2.REPEAT;
CREATE SCHEMA IF NOT EXISTS AMAR_WORKSHOP_P2.REJECTION;
CREATE SCHEMA IF NOT EXISTS AMAR_WORKSHOP_P2.REPAYMENT;
CREATE SCHEMA IF NOT EXISTS AMAR_WORKSHOP_P2.GEO;
SHOW SCHEMAS IN DATABASE AMAR_WORKSHOP_P2;
