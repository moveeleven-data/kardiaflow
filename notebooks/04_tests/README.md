# KardiaFlow Smoke Tests

End-to-end checks for Bronze, Silver, and Gold tables after each pipeline run.

Results are written to:  
**`kardia_validation.smoke_results`**

| Column      | Description                        |
|-------------|------------------------------------|
| `run_ts`    | Timestamp of test run              |
| `layer`     | `BRONZE`, `SILVER`, or `GOLD`      |
| `table_name`| Full Delta table name              |
| `metric`    | Validation type (e.g. `row_count`) |
| `value`     | Observed value                     |
| `status`    | `PASS`, `FAIL`, or `ERROR`         |
| `message`   | Optional notes / error details     |

---

## What It Checks

- **Bronze:**  
  - Rows > 0  
  - No null or duplicate PKs (unless suppressed)

- **Silver:**  
  - All expected columns are present

- **Gold:**  
  - Critical columns are non-null