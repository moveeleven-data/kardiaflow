# Patients & Encounters Ingestion

This pipeline ingests patient and encounter records into the Bronze, Silver, and
Gold layers of a Databricks Lakehouse. Patient data begins as raw CSV files, and
encounter data as raw Avro files. Both are uploaded to DBFS and ingested into Bronze
Delta tables using Auto Loader with predefined schemas. Change Data Feed (CDF) is
enabled on all Bronze tables to support efficient, incremental Silver-layer processing.

---

## Bootstrap: Raw Folder and File Setup

Run 99_bootstrap_raw_patients_encounters.ipynb to create the raw input folders and copy patients_part_1.csv and 
encounters_part_1.avro into their respective DBFS directories:
- dbfs:/kardia/raw/patients/
- dbfs:/kardia/raw/encounters/

To add more files later, use 99_move_new_pat_enc_files_to_raw.ipynb.


## Raw -> Bronze -> Silver **(Patients)**

1. Run 00_bronze_patients_autoloader.ipynb to ingest patient CSV files into kardia_bronze.bronze_patients using Auto Loader.

2. Run 01_validate_bronze_patients.ipynb to validate row counts, uniqueness, and nulls in the Bronze Patients table. This notebook also logs metadata to kardia_meta.bronze_qc.

3. Run 02_silver_patients_transform.ipynb to read from Bronze using CDF, deduplicate rows, mask PHI fields, derive BIRTH_YEAR, and upsert into kardia_silver.silver_patients.


## Raw -> Bronze -> Silver **(Encounters)**

1. Run 00_bronze_stream_encounters_autoloader.ipynb to ingest encounter Avro files into kardia_bronze.bronze_encounters using Auto Loader with .trigger(availableNow=True).

2. Run 01_validate_bronze_encounters.ipynb to validate Bronze Encounters data and append summary metrics to 
kardia_meta.bronze_qc.

3. Run 02_silver_encounters_transform.ipynb to stream inserts and updates using CDF and foreachBatch, parse timestamps, and upsert clean records into kardia_silver.silver_encounters.


## Silver (Stream-Static) Join: **Patients and Encounters**

- Run 02_silver_enc_demographics_join.ipynb to enrich each encounter with demographic fields from the Silver Patients 
 table and write the result to kardia_silver.silver_encounters_demographics.


## Gold: Gender Breakdown & Monthly Volumes

1. Run 03_gold_gender_breakdown.ipynb to compute the latest gender distribution and merge results into the Gold Gender 
Breakdown table.

2. Run 03_gold_encounters_by_month.ipynb to aggregate monthly encounter volumes and refresh supporting QA tables that track data completeness.

---

## Error Handling

The Bronze layer is built to load data quickly, even if some files are messy.
If a file is badly formatted, it gets quarantined so it doesn't stop the whole
pipeline. For patient CSVs, there's a special column (_rescued_data) that catches
extra or missing fields. Deeper cleanup (like fixing column issues or handling PHI)
happens later in the Silver layer.

In a real production setup, I’d add a step before ingestion that checks Avro files
for issues ahead of time. I’d also add alerts to notify the team if any files end
up in the quarantine folder.