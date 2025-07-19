# Data Dictionary: KardiaFlow Synthetic Healthcare Dataset

## Source Files

- `dbfs:/kardia/raw/claims/claims.csv`
- `dbfs:/kardia/raw/claims/providers.tsv`
- `dbfs:/kardia/raw/ehr/patients.csv`
- `dbfs:/kardia/raw/ehr/encounters.avro`
- `dbfs:/kardia/raw/feedback/feedback.json`
- `dbfs:/kardia/raw/feedback/device_data.json`

---

## File: `claims.csv`

| Field Name             | Type     | Description                                                             |
|------------------------|----------|-------------------------------------------------------------------------|
| `ClaimID`              | UUID     | Unique identifier for each insurance claim                              |
| `PatientID`            | UUID     | Foreign key to patient                                                  |
| `ProviderID`           | UUID     | Foreign key to provider                                                 |
| `ClaimAmount`          | Float    | Amount in USD                                                           |
| `ClaimDate`            | Date     | Date submitted (YYYY-MM-DD)                                             |
| `DiagnosisCode`        | String   | ICD or SNOMED-style code                                                |
| `ProcedureCode`        | String   | CPT or similar procedure code                                           |
| `ClaimStatus`          | Enum     | Approved, Denied, Pending                                               |
| `ClaimType`            | Enum     | Inpatient, Outpatient, Emergency, Routine                               |
| `ClaimSubmissionMethod`| Enum     | Online, Paper, Phone                                                    |

---

## File: `providers.tsv`

| Field Name             | Type     | Description                                                             |
|------------------------|----------|-------------------------------------------------------------------------|
| `ProviderID`           | UUID     | Unique identifier for provider                                          |
| `ProviderSpecialty`    | String   | Medical specialty (e.g., Oncology, Pediatrics)                          |
| `ProviderLocation`     | String   | City/State/Region                                                       |

---

## File: `patients.csv`

| Field Name   | Type   | Description                          |
|--------------|--------|--------------------------------------|
| `ID`         | UUID   | Unique patient ID                    |
| `BIRTHDATE`  | Date   | Date of birth                        |
| `DEATHDATE`  | Date   | If deceased, date of death           |
| `SSN`        | String | Synthetic SSN                        |
| `DRIVERS`    | String | Driver’s License                     |
| `PASSPORT`   | String | Passport ID                          |
| `PREFIX`     | String | Mr., Ms., Dr., etc.                  |
| `FIRST`      | String | First name                           |
| `LAST`       | String | Last name                            |
| `MARITAL`    | String | Marital status                       |
| `RACE`       | String | Race                                 |
| `ETHNICITY`  | String | Ethnicity                            |
| `GENDER`     | String | Gender (M/F)                         |
| `BIRTHPLACE` | String | City/State of birth                  |
| `ADDRESS`    | String | Street address                       |

---

## File: `encounters.avro`

| Field Name         | Type   | Description                              |
|--------------------|--------|------------------------------------------|
| `ID`               | UUID   | Unique identifier for the encounter      |
| `DATE`             | Date   | Encounter date                           |
| `PATIENT`          | UUID   | Foreign key to `patients.ID`             |
| `CODE`             | String | Encounter type code                      |
| `DESCRIPTION`      | String | Human-readable encounter description     |
| `REASONCODE`       | String | Reason code for the visit                |
| `REASONDESCRIPTION`| String | Description of the visit reason          |

---

## File: `feedback.json`

| Field Name         | Type     | Description                                 |
|--------------------|----------|---------------------------------------------|
| `patient_id`       | UUID     | Links to patient                            |
| `visit_id`         | UUID     | Optional join to encounter                  |
| `timestamp`        | ISODate  | When the feedback was recorded              |
| `satisfaction_score` | Integer | Rating from 1 to 5                         |
| `comments`         | String   | Free-form text                              |

---

## File: `device_data.json`

| Field Name   | Type     | Description                                   |
|--------------|----------|-----------------------------------------------|
| `patient_id` | UUID     | Links to patient                              |
| `timestamp`  | ISODate  | Timestamp of telemetry record                 |
| `heart_rate` | Integer  | Heart rate in BPM                             |
| `steps`      | Integer  | Number of steps                               |
| `device_id`  | String   | Unique device ID                              |

---

## Notes

- All data is synthetic and non-PHI
- Designed for Delta Lake and streaming pipeline testing
