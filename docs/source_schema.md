## Source Schema & Relationships

This file complements the [Data Dictionary](./data_dictionary.md) by describing
how the raw source entities relate, which identifier columns they expose, and how
they are joined before normalization.

---

### Identifiers (raw, non-enforced)

These columns are the record identifiers present in the raw files.

| Dataset    | Identifier    |
|------------|----------------|
| patients   | `ID`          |
| encounters | `ID`          |
| claims     | `ClaimID`     |
| providers  | `ProviderID`  |
| feedback   | `feedback_id` |

Notes: date fields arrive as text (`DATE`, `ClaimDate`); `feedback.timestamp` is ISO-8601 without an explicit timezone offset.

---

### Reference map (raw, non-enforced)

These are the reference columns and join predicates as they exist in raw.

| From       | To         | Join on                                       | Expected |
|------------|------------|-----------------------------------------------|----------|
| encounters | patients   | `encounters.PATIENT = patients.ID`            | m→1      |
| claims     | patients   | `claims.PatientID = patients.ID`              | m→1      |
| claims     | providers  | `claims.ProviderID = providers.ProviderID`    | m→1      |
| feedback   | encounters | `feedback.visit_id = encounters.ID`           | m→1      |
| feedback   | providers  | `feedback.provider_id = providers.ProviderID` | m→1      |

In practice, these references are sometimes null or point to missing rows. Normalization and validation happen in Silver and Gold.

---

### Semantics and timing (raw)

Patients and providers serve as relatively stable reference entities. Encounters and claims are event-like facts, each keyed by a date field (DATE, ClaimDate). Feedback is timestamped in ISO-8601 format and may reference both an encounter (visit_id) and a provider (provider_id). Because raw delivery is taken “as is,” sparsity is expected—for example, encounters missing a REASONCODE, feedback without comments, or claims pointing to patients that aren’t present.

---

### Naming and normalization notes

Raw preserves the source’s original casing and field names (ClaimID, PATIENT, ProviderID). In Silver we standardize: column names shift to snake_case, dates are promoted to proper DATE/TIMESTAMP types, and categorical fields are aligned to consistent enums. Silver is also where the canonical join logic is applied.

**Key normalization mapping (raw → silver names)**

| Raw key         | Silver key     |
|-----------------|----------------|
| `ClaimID`       | `claim_id`     |
| `PatientID`     | `patient_id`   |
| `ProviderID`    | `provider_id`  |
| `encounters.ID` | `encounter_id` |
| `encounters.PATIENT` | `patient_id` |
| `feedback.feedback_id` | `feedback_id` |
| `feedback.visit_id`    | `encounter_id` (join target) |
| `feedback.provider_id` | `provider_id`  |

---

### Integrity and nullability guidance

The raw layer does not enforce uniqueness or referential integrity. We routinely see orphaned facts such as claims with no matching patient or feedback tied to missing providers. To preserve events, all fact-to-dimension joins are implemented as left joins. Harder constraints—such as not-null enforcement and duplicate suppression—begin in Silver and Gold, where they are covered by the validation suite.

---

### Join recipes

Use these predicates when exploring Bronze or tracing lineage prior to normalization.

```sql
-- Claims → Patients (preserve all claims)
SELECT c.*, p.ID AS patient_pk
FROM claims c
LEFT JOIN patients p
  ON c.PatientID = p.ID;

-- Claims → Providers (raw attributes are static text fields)
SELECT c.*, pr.ProviderSpecialty, pr.ProviderLocation
FROM claims c
LEFT JOIN providers pr
  ON c.ProviderID = pr.ProviderID;

-- Feedback → Encounters and Providers (preserve all feedback)
SELECT f.*, e.ID AS encounter_pk, pr.ProviderSpecialty, pr.ProviderLocation
FROM feedback f
LEFT JOIN encounters e
  ON f.visit_id = e.ID
LEFT JOIN providers pr
  ON f.provider_id = pr.ProviderID;

-- Encounters → Patients (event → dimension)
SELECT e.*, p.ID AS patient_pk
FROM encounters e
LEFT JOIN patients p
  ON e.PATIENT = p.ID;
```