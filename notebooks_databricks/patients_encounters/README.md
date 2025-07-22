# Patients & Encounters Ingestion

This pipeline ingests patient and encounter records into a Databricks Lakehouse using Delta Lake and Auto Loader. All datasets land in a Bronze layer with Change Data Feed (CDF) enabled, are validated, then transformed into Silver and Gold layers for downstream analytics.

---

## Raw Bootstrap

Patient and encounter files are manually uploaded to DBFS:

- Patients: `dbfs:/kardia/raw/patients/patients_part_*.csv`
- Encounters: `dbfs:/kardia/raw/encounters/encounters_part_*.avro`

Run `99_bootstrap_raw_patients_encounters.ipynb` to initialize folders and copy sample files.  
Use `99_move_new_pat_enc_files_to_raw.ipynb` to add additional files later.

---

## Bronze Ingestion

| Dataset    | Source | Format | Loader      | Bronze Table                      |
|------------|--------|--------|-------------|-----------------------------------|
| Patients   | DBFS   | CSV    | Auto Loader | `kardia_bronze.bronze_patients`   |
| Encounters | DBFS   | Avro   | Auto Loader | `kardia_bronze.bronze_encounters` |

Each ingestion notebook reads raw files using a predefined schema, adds audit columns, and writes to a Bronze Delta table with CDF enabled.

---

## Silver Transformation

| Dataset    | Logic         | Silver Table                           |
|------------|---------------|----------------------------------------|
| Patients   | Batch SCD Type 1 | `kardia_silver.silver_patients`        |
| Encounters | Continuous Streaming | `kardia_silver.silver_encounters`      |

Join notebooks create enriched views:
- `silver_encounters_enriched`: Stream-static join of Silver encounters (streaming) with Silver patients (static) for demographic enrichment

---

## Gold KPIs

| Table                          | Description                                                        |
|--------------------------------|--------------------------------------------------------------------|
| `gold_patient_lifecycle`       | Visit intervals, patient lifespan, age bands, new/returning flags |

---

## Validation

Each Bronze table has a validation notebook to check row counts, nulls, uniqueness, and data quality. Results are logged to `kardia_validation.*_summary` tables.
