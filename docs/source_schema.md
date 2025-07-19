# Source Schema Overview

This file supplements the data dictionary by outlining how raw source datasets relate to one another structurally and semantically across different formats.

---

## 1. Entity Relationships (High-Level)

- **patients.csv** is the central table in the EHR dataset. It connects to:
  - `encounters.avro` via `patients.ID → encounters.PATIENT`

- **claims.csv** connects to:
  - `patients.csv` via `claims.PatientID → patients.ID`
  - `providers.tsv` via `claims.ProviderID → providers.ProviderID`

- **feedback.json** and **device_data.json** are loosely linked via:
  - `patient_id → patients.ID`
  - `visit_id → encounters.ID` (in `feedback.json` only)

---

## 2. Source File Types & Storage Format

| File(s)                 | Format       | Type             | Storage Location                |
|-------------------------|--------------|------------------|---------------------------------|
| patients_part_*.csv     | CSV          | Structured       | `dbfs:/kardia/raw/ehr/`         |
| encounters_part_*.avro  | Avro         | Structured       | `dbfs:/kardia/raw/ehr/`         |
| claims_part_*.csv       | CSV          | Structured       | `dbfs:/kardia/raw/claims/`      |
| providers.tsv           | TSV          | Structured       | `dbfs:/kardia/raw/claims/`      |
| feedback.json           | JSON array   | Semi-structured  | `dbfs:/kardia/raw/feedback/`    |
| device_data.json        | JSON array   | Semi-structured  | `dbfs:/kardia/raw/feedback/`    |

---

## 3. Intended Usage in Pipeline

- All files are ingested using **Databricks Auto Loader** into **Bronze Delta tables** on DBFS.
- Transformation logic occurs in **Silver** via CDF with deduplication, PHI masking, and constraint enforcement.
- Final Gold views are served directly from **Databricks Delta** and visualized using **Databricks SQL dashboards**.
