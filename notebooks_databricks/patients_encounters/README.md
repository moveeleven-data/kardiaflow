Patients & Encounters Ingestion

This pipeline ingests patient and encounter records into the Bronze, Silver, and Gold layers of a Databricks Lakehouse. Both flows begin with Auto Loader streaming raw CSVs into Bronze Delta tables using explicitly defined schemas. Change Data Feed (CDF) is enabled at the Bronze level to support incremental updates in Silver. All jobs run on a single-node cluster with no external services.

In the Bronze layer, .trigger(availableNow=True) is used for one-shot ingestion of files. In Silver, encounter data is streamed and upserted via foreachBatch with MERGE, while patient data is transformed with deduplication, PHI masking, and enrichment. In Gold, encounter volumes are aggregated and QA metrics are refreshed using incremental batch jobs.

Patients: Bronze to Silver

1. Run 99_bootstrap_raw_dirs_and_files.ipynb to create raw folders and move patients_10.csv into DBFS. For additional files, use 99_move_new_test_files_to_raw.ipynb.

2. Run 01_bronze_patients_autoloader.ipynb to ingest patient CSVs into kardia_bronze.bronze_patients using Auto Loader.

3. Run 02_silver_patients_transform.py to read CDF from Bronze, deduplicate, mask PHI fields, derive BIRTH_YEAR, and upsert into kardia_silver.silver_patients.

Encounters: Bronze to Silver to Gold

4. Ensure encounters_10.csv is in dbfs:/kardia/raw/encounters/ via the bootstrap or file-move notebook.

5. Run 01_bronze_stream_encounters_autoloader.ipynb to stream encounter CSVs into kardia_bronze.bronze_encounters.

6. Run 02_silver_encounters_transform.ipynb to stream inserts/updates from CDF, parse timestamps, and upsert into kardia_silver.silver_encounters.

7. Run 03_silver_enc_demographics_join.ipynb to join encounters with patient data and write enriched results to kardia_silver.silver_encounters_demographics.

8. Run 03_gold_encounters_by_month.ipynb to aggregate monthly counts into kardia_gold.gold_encounters_by_month and refresh two QA tables for data completeness.