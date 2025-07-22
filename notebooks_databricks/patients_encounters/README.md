# Patients & Encounters Ingestion

This pipeline ingests patient and encounter records into the Bronze, Silver, and
Gold layers of a Databricks Lakehouse. Patient data begins as raw CSV files, and
encounter data as raw Avro files. Both are uploaded to DBFS and ingested into Bronze
Delta tables using Auto Loader with predefined schemas. Change Data Feed is
enabled on all Bronze tables to support efficient, incremental Silver-layer processing.

---

## Bootstrap: Raw Folder and File Setup

Run 99_bootstrap_raw_patients_encounters.ipynb to create the raw input folders and copy patients_part_1.csv and 
encounters_part_1.avro into their respective DBFS directories:
- dbfs:/kardia/raw/patients/
- dbfs:/kardia/raw/encounters/

To add more files later, use 99_move_new_pat_enc_files_to_raw.ipynb.


## Raw -> Bronze -> Silver **(Patients)**

1. Run 00_bronze_patients_autoloader.ipynb to ingest patient CSV files into
kardia_bronze.bronze_patients using Auto Loader.

2. Run 01_validate_bronze_patients.ipynb to validate row counts, uniqueness,
and nulls in the Bronze Patients table. This notebook also logs metadata to kardia_meta.bronze_qc.

3. Run 02_silver_patients_transform.ipynb to read from Bronze using CDF,
deduplicate rows, mask PHI fields, derive BIRTH_YEAR, and upsert into kardia_silver.silver_patients.


## Raw -> Bronze -> Silver **(Encounters)**

1. Run 01_bronze_encounters_autoloader.ipynb to stream encounter Avro files into
kardia_bronze.bronze_encounters using Auto Loader.

2. Run 01_validate_bronze_encounters.ipynb to validate Bronze Encounters data and
append summary metrics to kardia_meta.bronze_qc.

3. Run 02_silver_encounters_transform.ipynb to consume CDF changes from Bronze, parse event timestamps,
and continuously upsert clean records into kardia_silver.silver_encounters.


## Silver Join: **Patients and Encounters**

- Run 02_silver_encounters_enriched.ipynb to enrich each encounter with
demographic fields from the Silver Patients table and write the result to
kardia_silver.silver_encounters_enriched.


## Gold: Gender Breakdown & Monthly Volumes

- Run 03_gold_patient_lifecycle.ipynb to track patient visit intervals, lifetime
span, age-band engagement, and new/returning classification.