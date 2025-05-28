## Data Dictionary: Enhanced Health Insurance Claims Dataset

### Source Files
- `data/raw/claims/claims.csv`
- `data/raw/claims/providers.csv`

### Dataset Overview
Synthetic dataset containing 4,500 health insurance claims. Designed to simulate real-world claim scenarios for analysis, ETL pipelines, validation, and machine learning. Generated using the Faker library to mimic real claim data without privacy risk.

---

### File: `claims.csv`

| Field Name             | Type     | Description                                                             |
|------------------------|----------|-------------------------------------------------------------------------|
| `ClaimID`              | UUID     | Unique identifier for each insurance claim                              |
| `PatientID`            | UUID     | Unique identifier for the patient associated with the claim             |
| `ProviderID`           | UUID     | Foreign key referencing the healthcare provider                         |
| `ClaimAmount`          | Float    | Amount claimed in USD                                                   |
| `ClaimDate`            | Date     | Date the claim was submitted (YYYY-MM-DD)                               |
| `DiagnosisCode`        | String   | Diagnosis code associated with the claim                                |
| `ProcedureCode`        | String   | Medical procedure performed                                             |
| `ClaimStatus`          | Enum     | Status of the claim (Approved, Denied, Pending)                         |
| `ClaimType`            | Enum     | Type of claim (Inpatient, Outpatient, Emergency, Routine)               |
| `ClaimSubmissionMethod`| Enum     | Method used to submit the claim (Online, Paper, Phone)                  |

`ProviderID` joins with `providers.csv`

---

### File: `providers.csv`

| Field Name             | Type     | Description                                                             |
|------------------------|----------|-------------------------------------------------------------------------|
| `ProviderID`           | UUID     | Unique identifier for the healthcare provider                           |
| `ProviderSpecialty`    | String   | Medical specialty of the provider (e.g., Cardiology, Pediatrics)        |
| `ProviderLocation`     | String   | City or region where the provider is located                            |

---

### Intended Use Cases
- ML prediction on `ClaimStatus`
- Fraud detection / anomaly detection
- Workflow testing for ETL validation and reconciliation
- Data governance simulations

---

### Notes
- Synthetic data generated with `Faker`; no real PHI is present
- Records reflect realistic formatting but do not represent real individuals

---

### File: `feedback.json`

| Field Name         | Type     | Description                                                        |
|--------------------|----------|--------------------------------------------------------------------|
| `patient_id`       | String   | Identifier of the patient who provided feedback                   |
| `visit_id`         | String   | Unique visit reference (may map to encounter in EHR data)         |
| `timestamp`        | ISODate  | Timestamp of the feedback submission                              |
| `satisfaction_score` | Integer | Rating from 1 (low) to 5 (high)                                    |
| `comments`         | String   | Free-text feedback about patient experience                       |

Notes:
- Stored as an array of JSON objects
- Useful for sentiment analysis or experience trends

---

### File: `device_data.json`

| Field Name         | Type     | Description                                                        |
|--------------------|----------|--------------------------------------------------------------------|
| `patient_id`       | String   | Identifier for the user wearing the device                         |
| `timestamp`        | ISODate  | Timestamp when the data was recorded                              |
| `heart_rate`       | Integer  | Beats per minute                                                   |
| `steps`            | Integer  | Number of steps taken since last sync                              |
| `device_id`        | String   | Unique identifier for the wearable device                          |

Notes:
- Can be used to simulate IoT stream ingestion
- Aligns well with Spark Structured Streaming or MongoDB pipelines

