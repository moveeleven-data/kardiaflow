# Source Schema Overview

This file supplements the data dictionary by outlining how raw source datasets relate to one another structurally and semantically across different formats.

---

## 1. Entity Relationships (High-Level)

- **patients.csv** is the central table in the EHR dataset. It connects to:
  - `encounters.csv` via `patients.ID → encounters.PATIENT`
  - `procedures.csv` via both:
    - `procedures.PATIENT → patients.ID`
    - `procedures.ENCOUNTER → encounters.ID`

- **claims.csv** connects to:
  - `patients.csv` via `claims.PatientID → patients.ID`
  - `providers.csv` via `claims.ProviderID → providers.ProviderID`

- **feedback.json** and **device_data.json** are loosely linked via:
  - `patient_id → patients.ID`
  - `visit_id → encounters.ID` (in `feedback.json` only)

---

## 2. Source File Types & Storage Format

| File(s)                | Format       | Type             | Storage Location                  |
|------------------------|--------------|------------------|-----------------------------------|
| patients.csv, etc.     | CSV          | Structured       | `data/raw/ehr/`                   |
| claims.csv, providers.csv | CSV       | Structured       | `data/raw/claims/`                |
| feedback.json          | JSON array   | Semi-structured  | `data/raw/feedback/feedback.json` |
| device_data.json       | JSON array   | Semi-structured  | `data/raw/feedback/device_data.json` |

---

## 3. Intended Usage in Pipeline

- All CSVs are ingested via **ADF Copy Activity** into **Bronze (ADLS Gen2)**.
- They are joined and transformed in **Silver (Databricks)** using `PatientID`, `ProviderID`, `ENCOUNTER`, and `visit_id`.
- Final cleaned tables are stored in **Gold (Azure SQL DB or PostgreSQL)**.

---
