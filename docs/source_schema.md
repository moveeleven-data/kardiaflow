## Source Entities and How They Relate

Complements the [Data Dictionary](./data_dictionary.md)
 by showing how raw entities relate through their identifiers and joins.

---

### Source Record Identifiers

These are the identifier columns from the source files that mark each record as unique, before any standardization.

| Dataset    | Identifier    |
|------------|----------------|
| patients   | `ID`          |
| encounters | `ID`          |
| claims     | `ClaimID`     |
| providers  | `ProviderID`  |
| feedback   | `feedback_id` |

Notes: date fields arrive as text (`DATE`, `ClaimDate`); `feedback.timestamp` is ISO-8601 with an explicit timezone offset.

---

### How the Raw Tables Connect

These columns show the links between tables in the raw data and how they can be joined.

| From       | To         | Join on                                       | Expected |
|------------|------------|-----------------------------------------------|----------|
| encounters | patients   | `encounters.PATIENT = patients.ID`            | m→1      |
| claims     | patients   | `claims.PatientID = patients.ID`              | m→1      |
| claims     | providers  | `claims.ProviderID = providers.ProviderID`    | m→1      |
| feedback   | providers  | `feedback.provider_id = providers.ProviderID` | m→1      |

---

### Data Quality in the Raw Layer

The raw layer does not guarantee uniqueness or enforce relationships between entities. As a result, orphan records are common—for example, claims referencing patients that are missing or feedback tied to absent providers. To preserve events, all fact-to-dimension joins are left joins, ensuring the event remains even without a matching reference. Stricter checks, such as non-null enforcement and duplicate suppression, are applied in the Silver and Gold layers.

---

### Standardizing Names and Formats

The raw layer reflects the source system exactly, keeping original field names and casing (e.g., ClaimID, PATIENT, 
ProviderID). In the Silver layer, these fields are standardized for consistency: column names are converted to snake_case, dates are cast to DATE or TIMESTAMP, and categorical values are standardized.

**Field Name Mapping (raw → silver)**

| Raw key         | Silver key     |
|-----------------|----------------|
| `ClaimID`       | `claim_id`     |
| `PatientID`     | `patient_id`   |
| `ProviderID`    | `provider_id`  |
| `encounters.ID` | `encounter_id` |
| `encounters.PATIENT` | `patient_id` |
| `feedback.feedback_id` | `feedback_id` |
| `feedback.provider_id` | `provider_id`  |

---

### How to Join the Data

Use these predicates when exploring Bronze or tracing lineage prior to normalization.

```sql
-- Join claims to patients.
-- Left join ensures all claims are kept even if the patient record is missing.
SELECT c.*,
       p.ID AS patient_pk
FROM claims c
LEFT JOIN patients p
       ON c.PatientID = p.ID;

-- Join claims to providers to enrich with provider details.
-- Provider attributes are static reference fields in the raw data.
SELECT c.*,
       pr.ProviderSpecialty,
       pr.ProviderLocation
FROM claims c
LEFT JOIN providers pr
       ON c.ProviderID = pr.ProviderID;

-- Join encounters to patients to connect each event with its patient.
-- Left join keeps encounter events even when the patient record is absent.
SELECT e.*,
       p.ID AS patient_pk
FROM encounters e
LEFT JOIN patients p
       ON e.PATIENT = p.ID;
```