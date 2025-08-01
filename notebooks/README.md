# Kardiaflow: Unified Health Data Pipeline

This project ingests synthetic healthcare data into a Databricks Lakehouse using
**Delta Lake**, **Auto Loader**, and a **medallion architecture**. It supports two core domains:

- **Encounters & Patients** — clinical events and demographics  
- **Claims, Providers & Feedback** — billing, metadata, and satisfaction

Test files are uploaded to **ADLS Gen2** in `/lake/{raw | providers | claims | feedback | patients}` folders, where 
they are picked up by Auto Loader pipelines.

All files are uploaded to **Azure Data Lake Storage Gen2 (ADLS)** under `/lake/kardia/...` paths, accessed via **OAuth2 
service principal authentication**.

### Raw File Paths

| Dataset     | ADLS Path                                                | Format  |
|-------------|----------------------------------------------------------|---------|
| Patients    | `abfss://lake@<storage>.dfs.core.windows.net/patients/`  | CSV     |
| Encounters  | `abfss://lake@<storage>.dfs.core.windows.net/encounters/` | Avro    |
| Claims      | `abfss://lake@<storage>.dfs.core.windows.net/claims/`     | Parquet |
| Providers   | `abfss://lake@<storage>.dfs.core.windows.net/providers/`  | TSV     |
| Feedback    | `abfss://lake@<storage>.dfs.core.windows.net/feedback/`   | JSONL   |

---

## Bronze Ingestion

Raw files are ingested into **Bronze Delta tables** using **Auto Loader** (or **COPY INTO** for JSONL formats). Each table includes:

Auto Loader is used for structured formats like CSV, Parquet, and TSV where incremental discovery and schema evolution are important. In contrast, COPY INTO is used for the semistructured JSONL Feedback data, where SQL-based projection, type coercion, and optional field handling are required during load.

- Audit columns: `_ingest_ts`, `_source_file`
- Change Data Feed (CDF) enabled
- Partitioning and schema enforcement

| Dataset     | Format   | Loader       | Bronze Table                      |
|-------------|----------|--------------|-----------------------------------|
| Patients    | CSV      | Auto Loader  | `kardia_bronze.bronze_patients`   |
| Encounters  | Avro     | Auto Loader  | `kardia_bronze.bronze_encounters` |
| Claims      | Parquet  | Auto Loader  | `kardia_bronze.bronze_claims`     |
| Providers   | TSV      | Auto Loader  | `kardia_bronze.bronze_providers`  |
| Feedback    | JSONL    | COPY INTO    | `kardia_bronze.bronze_feedback`   |

All Bronze tables include:

- Audit columns: `_ingest_ts`, `_source_file`, `_batch_id`
- Schema enforcement + CDF (Change Data Feed) enabled

---

## Silver Transformation

Silver notebooks apply:

- **Deduplication** and **SCD logic**  
- **PHI masking**

| Dataset     | Method               | Silver Table                        |
|-------------|----------------------|-------------------------------------|
| Patients    | Batch SCD Type 1     | `kardia_silver.silver_patients`     |
| Encounters  | Continuous Streaming | `kardia_silver.silver_encounters`   |
| Claims      | SCD Type 1           | `kardia_silver.silver_claims`       |
| Providers   | SCD Type 2           | `kardia_silver.silver_providers`    |
| Feedback    | Append-only          | `kardia_silver.silver_feedback`     |

### Enriched Silver Views

| View Name                    | Description                                      |
|-----------------------------|--------------------------------------------------|
| `silver_encounters_enriched`| Encounters joined with patient demographics      |
| `silver_claims_enriched`    | Claims joined with current provider attributes   |
| `silver_feedback_enriched`  | Feedback joined with current provider metadata   |

---

## Gold KPIs

Gold notebooks generate business-level aggregations for analytics and dashboards:

| Table Name                    | Description                                                  |
|------------------------------|--------------------------------------------------------------|
| `gold_patient_lifecycle`     | Visit intervals, patient lifespan, new/returning flags       |
| `gold_claim_anomalies`       | Approval rates, denials, high-cost procedures               |
| `gold_provider_rolling_spend`| Daily spend and 7-day rolling KPIs for provider payments     |
| `gold_feedback_metrics`      | Satisfaction tags, comment analysis, sentiment scoring       |

---

## Validation

Validation logic is built into `kflow.validation`, invoked via `run_smoke.py`. Results are written to 
`kardia_validation.smoke_results`.

- **Bronze:** Row counts, PK nulls/dupes, `_ingest_ts`
- **Silver:** Schema contract compliance
- **Gold:** Not-null critical fields

---

## Streaming Modes

The **Encounters pipeline** supports runtime switching between batch and stream:

| Mode   | Behavior                                      |
|--------|-----------------------------------------------|
| `batch`| One-time read of all available data           |
| `stream`| Continuous micro-batches every 30 seconds    |

Only the **Encounters pipeline** supports this parameter:

- `bronze_encounters_autoloader`
- `silver_encounters_scd1`
- `z_silver_encounters_enriched`

All other datasets (Patients, Claims, Providers, Feedback) run in batch mode and are unaffected.

---

### How to set it

In the Databricks Job UI:

1. Open the job `KardiaFlow_Demo_FullRun`
2. For each Encounters-related task, add a parameter:

> Key: mode

> Value: batch or stream

You can leave the parameter out for batch tasks — they will ignore it.