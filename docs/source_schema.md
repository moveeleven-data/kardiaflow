# Source Schema Overview

This file supplements the data dictionary by outlining how raw source datasets relate to one another structurally and semantically across different formats.

---

## 1. Entity Relationships (High-Level)

- **patients.csv** is the central table in the EHR dataset. It connects to:
  - `encounters.avro` via `patients.ID → encounters.PATIENT`

- **claims.parquet** connects to:
  - `patients.csv` via `claims.PatientID → patients.ID`
  - `providers.tsv` via `claims.ProviderID → providers.ProviderID`

- **feedback.json** and **device_data.json** are loosely linked via:
  - `patient_id → patients.ID`
  - `visit_id → encounters.ID` (in `feedback.json` only)

---

## 2. Source File Types & Storage Format

| File(s)                | Format     | Type             | Storage Location                |
|------------------------|------------|------------------|---------------------------------|
| patients_part_*.csv    | CSV        | Structured       | `dbfs:/kardia/raw/ehr/`         |
| encounters_part_*.avro | Avro       | Structured       | `dbfs:/kardia/raw/ehr/`         |
| claims_part_*.parquet  | Parquet    | Structured       | `dbfs:/kardia/raw/claims/`      |
| providers_part_*.tsv   | TSV        | Structured       | `dbfs:/kardia/raw/claims/`      |
| feedback_part_*.json   | JSON array | Semi-structured  | `dbfs:/kardia/raw/feedback/`    |

---

## 3. Intended Usage in Pipeline

All files are ingested into Bronze Delta tables on DBFS. Most use Databricks Auto Loader to support scalable, schema-evolving ingestion. The feedback flow, however, uses COPY INTO for simplicity and compatibility with JSON array files, as it involves lower data quality risk and does not require the full governance and streaming features applied to core datasets.
- Silver-layer transformations apply Change Data Feed (CDF), deduplication, PHI masking, and constraint enforcement 
to produce clean, enriched Delta tables.
- Gold tables serve as the primary analytical surface, powering Databricks SQL dashboards and downstream reporting 
use cases.
