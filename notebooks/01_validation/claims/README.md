# Validation: Claims, Providers & Feedback (Bronze)

This module performs post-ingestion validation for the **Claims**, **Providers**, and **Feedback** datasets after they land in the Bronze layer. It uses a unified validation utility to compute custom metrics and log summaries to Delta Lake tables.

Validation is performed via dedicated notebooks:
- `01_validate_bronze_claims.ipynb`
- `01_validate_bronze_providers.ipynb`
- `01_validate_bronze_feedback.ipynb`

---

## Scope

Each notebook performs:
- Row-level profiling on key business fields
- Null count tracking on important dimensions
- Outlier or domain-specific checks (e.g., negative claim amounts)
- Logging to dedicated validation summary tables

No downstream logic (e.g. Silver joins or transformations) is executed during validation.

---

## Dataset-Specific Checks

### 🔸 Bronze Claims

| Field Checked      | Metric                        |
|--------------------|-------------------------------|
| `PatientID`        | Null count                    |
| `ClaimAmount`      | Min, Max, Negative amount count |

Output Table:  
`kardia_validation.bronze_claims_summary`

### 🔸 Bronze Providers

| Field Checked         | Metric          |
|------------------------|----------------|
| `ProviderSpecialty`    | Null count     |
| `ProviderLocation`     | Null count     |

Output Table:  
`kardia_validation.bronze_providers_summary`

### 🔸 Bronze Feedback

| Field Checked          | Metric          |
|------------------------|----------------|
| `satisfaction_score`   | Null count     |

Output Table:  
`kardia_validation.bronze_feedback_summary`

---

## Implementation Notes

All notebooks follow a consistent validation structure:

1. Load table using `spark.table(...)`
2. Define `extra_metrics` using Spark SQL expressions
3. Call `validate_and_log()` from `kflow.validation_utils`:
   - Logs summary stats to Delta
   - Uses primary key for duplicate detection
   - Supports optional assertions (not used here)
4. Display success banner

Example (Claims):
```python
validate_and_log(df,
                 table_name="bronze_claims",
                 pk_col="ClaimID",
                 extra_metrics=extra,
                 assertions=None)
```

---