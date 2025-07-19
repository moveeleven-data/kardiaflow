# Claims & Providers Ingestion

This pipeline ingests two datasets into the Bronze layer of a Databricks Lakehouse:
provider metadata (via TSV files in ADLS Gen2 using Auto Loader) and synthetic health
claims (via Avro files stored in DBFS). Provider files are stored in an Azure Data
Lake Storage Gen2 container, and Auto Loader accesses them using a SAS token stored
securely in a Databricks secret scope.

---

## Bootstrap: Raw Folder and File Setup

Run 99_bootstrap_raw_claims.ipynb to create the raw input folder and copy claims_part_1.avro into the DBFS directory:
- dbfs:/kardia/raw/claims/

To add more files later, use 99_move_new_claim_files_to_raw.ipynb.


## ADLS Gen2 -> Bronze -> Silver **(Providers)**

1. Upload providers.tsv to the ADLS Gen2 container raw, under the path: raw/providers/providers.tsv. The workspace accesses this path via managed identity or SAS token.

2. Run 01_bronze_stream_providers_autoloader.ipynb to ingest provider TSV files into kardia_bronze.bronze_providers using Auto Loader. The ingestion reads directly from Azure Data Lake Storage Gen2 using Azure Blob File System paths with managed identity authentication.

3. Run 01_validate_bronze_providers.ipynb to validate the Bronze Providers table. This performs row-level checks and adds a summary to kardia_meta.bronze_qc, but will not halt the pipeline if validation fails.

4. Run 02_silver_providers_transform.ipynb to batch read from Bronze, apply SCD Type 2 logic, and write deduplicated provider records to kardia_silver.silver_providers.


## DBFS -> Bronze -> Silver **(Claims)**

1. Run 99_bootstrap_raw_dirs_and_files.ipynb to copy the uploaded claims_part_1.avro file into the Auto Loader watch directory:
dbfs:/kardia/raw/claims/.

2. Run 01_bronze_stream_claims_autoloader.ipynb to ingest claim Avro files into kardia_bronze.bronze_claims using Auto Loader. The pipeline infers the schema from Avro metadata and stores it for reuse, appending new data incrementally with Change Data Feed enabled.

3. Run 01_validate_bronze_claims.ipynb to perform null, uniqueness, and value-range checks on the Bronze Claims table. The validation results are logged to kardia_meta.bronze_qc.

4. Run 02_silver_claims_transform.ipynb to read from Bronze, apply SCD Type 1 logic, and write the cleansed data into kardia_silver.silver_claims.


## Silver Join: **Claims and Providers**

- Run 02_silver_claims_enriched_join.ipynb to join Silver claims with Silver providers and write enriched results to kardia_silver.silver_claims_enriched.


## Gold: Hourly Metrics and Provider Spend

- Run 03_gold_claims_metrics.ipynb to compute hourly claim volumes and 7-day rolling spend metrics, saving the results to Gold tables.
