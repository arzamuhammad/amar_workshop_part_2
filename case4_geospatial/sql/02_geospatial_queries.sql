/* ============================================================================
   CASE 4 — GEOSPATIAL | 02_geospatial_queries.sql
   Kumpulan query referensi (versi SQL dari notebook). Fungsi native Snowflake.
   ============================================================================ */
USE DATABASE AMAR_WORKSHOP_P2; USE SCHEMA GEO;

-- 1) Titik GEOGRAPHY dari lat/long (urut: longitude, latitude) --------------
SELECT customer_id, ST_ASWKT(ST_MAKEPOINT(longitude, latitude)) AS geo_point
FROM CUSTOMERS_GEO LIMIT 5;

-- 2) COVERAGE: jarak nasabah -> layanan terdekat (ST_DISTANCE, meter) --------
CREATE OR REPLACE TABLE CUSTOMER_COVERAGE AS
WITH c AS (SELECT customer_id, city, latitude, longitude, ST_MAKEPOINT(longitude,latitude) g FROM CUSTOMERS_GEO),
     s AS (SELECT ST_MAKEPOINT(longitude,latitude) g FROM SERVICE_POINTS)
SELECT c.customer_id, c.city, c.latitude, c.longitude,
       MIN(ST_DISTANCE(c.g, s.g))/1000 AS nearest_km,
       IFF(MIN(ST_DISTANCE(c.g, s.g))/1000 > 5, 1, 0) AS underserved
FROM c CROSS JOIN s GROUP BY 1,2,3,4;

SELECT city, ROUND(AVG(nearest_km),2) avg_km, SUM(underserved) underserved
FROM CUSTOMER_COVERAGE GROUP BY 1 ORDER BY 2 DESC;

-- 3) Center point konsentrasi nasabah per kota (ST_CENTROID/ST_COLLECT) ------
SELECT city,
       ST_ASWKT(ST_CENTROID(ST_COLLECT(ST_MAKEPOINT(longitude, latitude)))) AS center_point,
       COUNT(*) n
FROM CUSTOMERS_GEO GROUP BY 1;

-- 4) H3 hexagon: sebaran & default rate (res 7) -----------------------------
SELECT H3_LATLNG_TO_CELL_STRING(latitude, longitude, 7) AS h3,
       COUNT(*) n_customers, ROUND(AVG(default_flag)*100,1) default_rate
FROM CUSTOMERS_GEO GROUP BY 1 ORDER BY n_customers DESC LIMIT 10;

-- 5) GEO-FRAUD A: fraud ring (cluster titik sama, H3 res 9 ~174m) -----------
SELECT H3_LATLNG_TO_CELL_STRING(latitude, longitude, 9) h3,
       COUNT(*) n_apps, COUNT(DISTINCT customer_id) n_cust
FROM LOAN_APPLICATIONS_GEO GROUP BY 1 ORDER BY n_apps DESC LIMIT 10;

-- 6) GEO-FRAUD B: impossible travel (>100km dalam <180 menit) ---------------
WITH a AS (
  SELECT customer_id, submit_ts, latitude, longitude,
         LAG(submit_ts) OVER (PARTITION BY customer_id ORDER BY submit_ts) prev_ts,
         LAG(latitude)  OVER (PARTITION BY customer_id ORDER BY submit_ts) prev_lat,
         LAG(longitude) OVER (PARTITION BY customer_id ORDER BY submit_ts) prev_lon
  FROM LOAN_APPLICATIONS_GEO)
SELECT customer_id, prev_ts, submit_ts,
       ROUND(ST_DISTANCE(ST_MAKEPOINT(longitude,latitude), ST_MAKEPOINT(prev_lon,prev_lat))/1000,1) dist_km,
       DATEDIFF('minute', prev_ts, submit_ts) mins
FROM a
WHERE prev_ts IS NOT NULL
  AND ST_DISTANCE(ST_MAKEPOINT(longitude,latitude), ST_MAKEPOINT(prev_lon,prev_lat))/1000 > 100
  AND DATEDIFF('minute', prev_ts, submit_ts) < 180
ORDER BY dist_km DESC;
