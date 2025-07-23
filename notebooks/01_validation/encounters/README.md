# Validation: Encounters & Patients (Bronze)

This module performs post-ingestion validation for the **Encounters** and **Patients** datasets immediately after they land in the Bronze layer. It uses a shared validation utility to compute custom metrics and log results to Delta summary tables for quality monitoring.

Validation is performed via the following notebooks:
- `01_validate_bronze_encounters.ipynb`
- `01_validate_bronze_patients.ipynb`

---

## Scope

Each validation notebook performs:
- Field-level profiling and health checks
- Null value tracking on critical fields
- Domain-specific rules (e.g., gender validity)
- Logging of results to structured Delta tables

No Silver logic or transformations are involved in this stage.

---

## Dataset-Specific Checks

### 🔸 Bronze Encounters

| Field Checked | Metric                      |
|---------------|-----------------------------|
| `PATIENT`     | Null count                  |
| `DATE`        | Null count                  |

Output Table:  
`kardia_validation.bronze_encounters_summary`

### 🔸 Bronze Patients

| Field Checked | Metric                        |
|---------------|-------------------------------|
| `GENDER`      | Count of invalid values (non-M/F) |

Output Table:  
`kardia_validation.bronze_patients_summary`

---

## Implementation Notes

All validations follow the same structure:

1. Load Bronze Delta table from path (`bronze_path(...)`)
2. Define `extra_metrics` using Spark SQL expressions
3. Use `validate_and_log()` from `kflow.validation_utils` to compute metrics and persist results

Example (Patients):
```python
validate_and_log(df,
                 table_name="bronze_patients",
                 pk_col="ID",
                 extra_metrics=extra,
                 assertions=None)
```

---