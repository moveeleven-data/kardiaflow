## Data Dictionary: Kardiaflow Synthetic Healthcare Dataset

This document lists fields, formats, and parsing notes for each raw dataset.  
For entity identifiers, join predicates, and normalization mapping, see the [Source Schema](./source_schema.md).

### Source Files (ADLS Gen2)

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

### File: `claims.parquet`

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

**Notes:**

- **Codes:** Diagnosis and procedure codes arrive as mixed-case alphanumerics (e.g., `yy006`, `tD052`). They are kept 
exactly as provided, without uppercasing or padding.  

- **Amounts and dates:** Claim amounts come in as decimals (e.g., `3807.95`). Claim dates follow `YYYY-MM-DD`; if a 
date cannot be parsed, it is stored as `NULL` while the record itself remains.  

- **Status and type fields:** Values such as claim status (`Pending`, `Approved`) and type (`Routine`, `Emergency`) 
look consistent but are not strictly standardized, so small variations may occur.  


---

### File: `providers.tsv`

| Field Name          | Type   | Description                         |
|---------------------|--------|-------------------------------------|
| `ProviderID`        | String (UUID) | Provider identifier             |
| `ProviderSpecialty` | String | Medical specialty (e.g., Cardiology)|
| `ProviderLocation`  | String | City/State/Region text              |

**Notes:**

- **Location field:** Provider locations come through as free-text city names (e.g., `Rowlandfurt`), without state or 
country.

- **Specialty field:** Specialties such as `Cardiology` or `Orthopedics` are free-text and unstandardized, so 
spelling and case variations appear as distinct values.  

- **Data quality:** Records missing a `ProviderID` are dropped, and malformed lines are redirected to the bad-records 
path, so only valid rows continue downstream.  

---

### File: `patients.csv`

| Field Name   | Type   | Description               |
|--------------|--------|---------------------------|
| `ID`         | String (UUID) | Unique patient ID    |
| `BIRTHDATE`  | Date (text) | `YYYY-MM-DD`         |
| `DEATHDATE`  | Date (text) | `YYYY-MM-DD` |
| `SSN`        | String | Synthetic SSN             |
| `DRIVERS`    | String | Driver’s License          |
| `PASSPORT`   | String | Passport ID               |
| `PREFIX`     | String | Mr., Ms., Dr., etc.       |
| `FIRST`      | String | First name                |
| `LAST`       | String | Last name                 |
| `SUFFIX`     | String | Name suffix   |
| `MAIDEN`     | String | Maiden name   |
| `MARITAL`    | String | Marital status            |
| `RACE`       | String | Race                      |
| `ETHNICITY`  | String | Ethnicity                 |
| `GENDER`     | String | Gender               |
| `BIRTHPLACE` | String | City/State of birth       |
| `ADDRESS`    | String | Street address            |

**Notes:**

- **Addresses and birthplace:** These fields sometimes include commas or territory codes (e.g., `GU`, `PR`). They are 
quoted and left unstandardized.

- **Sensitive data:** Personally identifiable details such as SSN, passport, and address are masked in Silver. 
Derived fields like `birth_year` remain available.  

---

### File: `encounters.avro`

| Field Name          | Type        | Description                                  |
|---------------------|-------------|----------------------------------------------|
| `ID`                | String (UUID) | Encounter identifier                         |
| `DATE`              | Date (text) | `YYYY-MM-DD`                                 |
| `PATIENT`           | String (UUID) | References `patients.ID`                     |
| `CODE`              | String      | Encounter type code                          |
| `DESCRIPTION`       | String      | Human-readable description                   |
| `REASONCODE`        | String      | Reason code for the visit       |
| `REASONDESCRIPTION` | String      | Text for the visit reason     |

**Notes:**

- **Reason fields:** Many rows lack a `REASONCODE` or `REASONDESCRIPTION`; these simply come through as `NULL`.

- **Dates:** Encounter dates are provided in `YYYY-MM-DD`. Invalid dates are set to `NULL`, but the encounter itself 
is preserved so that patient joins are not broken.

---

### File: `feedback.jsonl`

| Field Name           | Type             | Description                                               |
|----------------------|------------------|-----------------------------------------------------------|
| `feedback_id`        | String (UUID)      | Feedback identifier                                       |
| `provider_id`        | String (UUID)      | References `providers.ProviderID`                         |
| `timestamp`          | ISO-8601 string  | Submission time with explicit offset               |
| `visit_id`           | String (UUID)      | References `encounters.ID`                   |
| `satisfaction_score` | Integer          | 1–5                                                       |
| `comments`           | String           | Free-form text                                  |
| `source`             | String           | `"in_clinic"`, `"web_portal"`, `"mobile_app"`   |
| `tags`               | Array<String>    | Category labels                                  |
| `metadata`           | Object           | Additional structured data                        |

**Notes**

- **Timestamps:** Each feedback record includes an ISO-8601 timestamp with an explicit offset (or Z). Bronze stores the raw string. Silver parses it to UTC (session fixed to UTC), ensuring daylight savings and offsets are applied correctly. Naïve timestamps are not permitted.

- **Comments field:** Free-text may contain sensitive details. Comments are retained only in Bronze for raw fidelity 
  and is not propagated to Silver or Gold.

- **Tags and metadata:** Tags appear sparsely (e.g., `["staff"]`, `["parking"]`) and are stored as arrays of strings 
without normalization. Metadata fields (e.g., `response_time_ms`) arrive as text and can be cast later if needed.