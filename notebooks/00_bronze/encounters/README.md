# Bronze Ingestion: Encounters & Patients

Ingests raw **patient** and **encounter** records into Delta tables in the
`kardia_bronze` schema using **Auto Loader** with **Change Data Feed (CDF)**
and audit columns. Paths and options come from `kflow.config.bronze_paths()`.

> We co-locate **patients** and **encounters** here because the primary grain for CDC and joins is **encounter-driven**.

For field definitions and relationships, see the
[Data Dictionary](../../../docs/data_dictionary.md) and [Source Schema](../../../docs/source_schema.md).

---

## Datasets

| Dataset    | Source (ABFSS)                                              | Format | Loader       | Bronze Table                        |
|-----------:|--------------------------------------------------------------|--------|--------------|-------------------------------------|
| Patients   | `abfss://lake@<storage>.dfs.core.windows.net/patients/`     | CSV    | Auto Loader  | `kardia_bronze.bronze_patients`     |
| Encounters | `abfss://lake@<storage>.dfs.core.windows.net/encounters/`   | Avro   | Auto Loader  | `kardia_bronze.bronze_encounters`   |

---

## Features

- **CDF** enabled on all Bronze tables  
- Audit columns: `_ingest_ts`, `_source_file`, `_batch_id`  
- Config-driven schema, checkpoint, and quarantine paths  
- **Patients**: incremental batch (**Trigger.AvailableNow**)  
- **Encounters** `mode` parameter:
  - `batch` → AvailableNow
  - `stream` → `trigger(processingTime="30 seconds")`
- Explicit schema enforcement for both formats

---

## Notebooks

| Notebook                                   | Target Table        | Trigger / Mode         |
|--------------------------------------------|---------------------|------------------------|
| [`bronze_patients_autoloader.ipynb`](./bronze_patients_autoloader.ipynb)     | `bronze_patients`   | Incremental batch      |
| [`bronze_encounters_autoloader.ipynb`](./bronze_encounters_autoloader.ipynb) | `bronze_encounters` | `mode=batch` or `stream` |

> Use the `mode` widget in Databricks (`dbutils.widgets.text("mode","batch")`) or pass as a job parameter.