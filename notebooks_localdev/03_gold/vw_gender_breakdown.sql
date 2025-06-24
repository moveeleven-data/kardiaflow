-- vw_gender_breakdown.sql
-- Builds a KPI view on top of the Silver Delta table.
-- Works for both dev (local paths) and prod (DBFS paths).

/* Path-based Delta → temp view */
CREATE OR REPLACE TEMP VIEW tmp_silver_patients AS
SELECT *
FROM delta.`${silver_patients_path}`;      -- substituted at runtime

/* KPI view over that temp view */
CREATE OR REPLACE VIEW vw_gender_breakdown AS
SELECT
    GENDER,
    COUNT(*) AS cnt
FROM
    tmp_silver_patients
GROUP BY
    GENDER;
