# Data Dictionary: Kardiaflow Synthetic Healthcare Dataset

This document lists fields, formats, and parsing notes for each raw dataset.  
For entity identifiers, join predicates, and normalization mapping, see the [Source Schema & Relationships](./source_schema.md).

## Source Files (ADLS Gen2)

We bootstrap the raw/source folders programmatically from repo samples.

- Container root: `lake`
- Source root: `lake/source`
- Datasets created: `encounters`, `claims`, `patients`, `providers`, `feedback`

| Dataset    | Path (within /source)     | Format  |
|------------|----------------------------|---------|
| Patients   | `/patients/*.csv`          | CSV     |
| Encounters | `/encounters/*.avro`       | Avro    |
| Claims     | `/claims/*.parquet`        | Parquet |
| Providers  | `/providers/*.tsv`         | TSV     |
| Feedback   | `/feedback/*.jsonl`        | JSONL   |

---

## File: `claims.parquet`

| Field Name              | Type        | Description                                    |
|-------------------------|-------------|------------------------------------------------|
| `ClaimID`               | String (UUID) | Unique identifier for each insurance claim     |
| `PatientID`             | String (UUID) | Reference to patient                           |
| `ProviderID`            | String (UUID) | Reference to provider                          |
| `ClaimAmount`           | Float       | Amount in USD                                  |
| `ClaimDate`             | Date (text) | `YYYY-MM-DD`                                   |
| `DiagnosisCode`         | String      | ICD/SNOMED-style code                          |
| `ProcedureCode`         | String      | CPT or similar procedure code                  |
| `ClaimStatus`           | Enum        | Approved, Denied, Pending                      |
| `ClaimType`             | Enum        | Inpatient, Outpatient, Emergency, Routine      |
| `ClaimSubmissionMethod` | Enum        | Online, Paper, Phone                           |

---

## File: `providers.tsv`

| Field Name          | Type   | Description                         |
|---------------------|--------|-------------------------------------|
| `ProviderID`        | String (UUID) | Provider identifier             |
| `ProviderSpecialty` | String | Medical specialty (e.g., Cardiology)|
| `ProviderLocation`  | String | City/State/Region text              |

---

## File: `patients.csv`

| Field Name   | Type   | Description               |
|--------------|--------|---------------------------|
| `ID`         | String (UUID) | Unique patient ID    |
| `BIRTHDATE`  | Date (text) | `YYYY-MM-DD`         |
| `DEATHDATE`  | Date (text) | `YYYY-MM-DD` or empty|
| `SSN`        | String | Synthetic SSN             |
| `DRIVERS`    | String | Driver’s License          |
| `PASSPORT`   | String | Passport ID               |
| `PREFIX`     | String | Mr., Ms., Dr., etc.       |
| `FIRST`      | String | First name                |
| `LAST`       | String | Last name                 |
| `SUFFIX`     | String | Name suffix (if present)  |
| `MAIDEN`     | String | Maiden name (if present)  |
| `MARITAL`    | String | Marital status            |
| `RACE`       | String | Race                      |
| `ETHNICITY`  | String | Ethnicity                 |
| `GENDER`     | String | Gender (M/F)              |
| `BIRTHPLACE` | String | City/State of birth       |
| `ADDRESS`    | String | Street address            |

Notes: Some fields (such as `BIRTHPLACE` and `ADDRESS`) are enclosed in quotes when they contain commas. The file mixes quoted and unquoted values, and Auto Loader parses them correctly by applying standard CSV quoting (commas inside quotes are treated as part of the field).

---

## File: `encounters.avro`

| Field Name          | Type        | Description                                  |
|---------------------|-------------|----------------------------------------------|
| `ID`                | String (UUID) | Encounter identifier                         |
| `DATE`              | Date (text) | `YYYY-MM-DD`                                 |
| `PATIENT`           | String (UUID) | References `patients.ID`                     |
| `CODE`              | String      | Encounter type code                          |
| `DESCRIPTION`       | String      | Human-readable description                   |
| `REASONCODE`        | String      | Reason code for the visit (often blank)      |
| `REASONDESCRIPTION` | String      | Text for the visit reason (often blank)      |

---

## File: `feedback.jsonl`

| Field Name           | Type             | Description                                                |
|----------------------|------------------|------------------------------------------------------------|
| `feedback_id`        | String (UUID)      | Feedback identifier                                        |
| `provider_id`        | String (UUID)      | References `providers.ProviderID`                          |
| `timestamp`          | ISO-8601 (text)  | Submission time; no explicit timezone offset               |
| `visit_id`           | String (UUID)      | References `encounters.ID` (when present)                  |
| `satisfaction_score` | Integer          | 1–5                                                        |
| `comments`           | String           | Free-form text (optional)                                  |
| `source`             | String           | `"in_clinic"`, `"web_portal"`, `"mobile_app"` (optional)   |
| `tags`               | Array<String>    | Category labels (optional)                                 |
| `metadata`           | Object           | Additional structured data (optional)                      |