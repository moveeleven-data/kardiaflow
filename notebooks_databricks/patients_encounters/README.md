Patients & Encounters Ingestion

This pipeline ingests patient and encounter records into the Bronze, Silver, and Gold layers of a Databricks Lakehouse. Both flows begin with Auto Loader streaming raw CSVs into Bronze Delta tables using explicitly defined schemas. Change Data Feed (CDF) is enabled at the Bronze level to support incremental updates in Silver. All jobs run on a single-node cluster with no external services.

In the Bronze layer, .trigger(availableNow=True) is used for one-shot ingestion of files. In Silver, encounter data is streamed and upserted via foreachBatch with MERGE, while patient data is transformed with deduplication, PHI masking, and enrichment. In Gold, encounter volumes are aggregated and QA metrics are refreshed using incremental batch jobs.

---

Bootstrap: DBFS to Raw landing zone

- Run 99_bootstrap_raw_dirs_and_files.ipynb to create raw folders and move patients.csv and encounters.csv into DBFS.

NOTE: For additional files, use 99_move_new_test_files_to_raw.ipynb.


Patients: Raw to Bronze to Silver

1. Run 00_bronze_patients_autoloader.ipynb to ingest patient CSVs into kardia_bronze.bronze_patients using Auto Loader.

2. Run 01_validate_bronze_patients to run basic assertions on Bronze Patients table. This is non-blocking and will not fail the pipeline if issues are found.

3. Run 02_silver_patients_transform.py to read CDF from Bronze, deduplicate, mask PHI fields, derive BIRTH_YEAR, and upsert into kardia_silver.silver_patients.


Encounters: Raw to Bronze to Silver

1. Run 00_bronze_stream_encounters_autoloader.ipynb to stream encounter Excel (XLSX) files into kardia_bronze.
   bronze_encounters.

2. Run 01_validate_bronze_patients to run basic assertions on Bronze Patients table. This is non-blocking and will not fail the pipeline if issues are found.

3. Run 02_silver_encounters_transform.ipynb to stream inserts/updates from CDF, parse timestamps, and upsert into kardia_silver.silver_encounters.


Silver (Stream-Static) Join: Patients and Encounters

- Run 02_silver_enc_demographics_join.ipynb to join encounters with patient data and write enriched results to kardia_silver.silver_encounters_demographics.


Gold: Gender Breakdown & Encounters by Month

1. Run 03_gold_gender_breakdown to compute the latest gender counts and MERGE them into the Gold Gender Breakdown table.

2. Run 03_gold_encounters_by_month.ipynb to aggregate monthly counts and refresh two QA tables that measure data completeness.