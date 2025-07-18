Providers & Claims Ingestion

This pipeline ingests two datasets into the Bronze layer of a Databricks Lakehouse:
provider metadata (via CSV files in ADLS Gen2 using Auto Loader) and synthetic health
claims (via Avro files and Auto Loader). The provider data now resides in the raw 
container of an Azure Data Lake Storage Gen2 account and Auto Loader ingests it
using a SAS token stored securely in a Databricks secret scope.

NOTE: All source files (except Providers) and every Delta table are stored in DBFS object storage,
which is encrypted at rest automatically. Reads and writes between the cluster
and that object store travel over TLS-encrypted HTTPS, so those stages are also
encrypted in transit. Inside the cluster, one path remains unencrypted: Spark
shuffle/broadcast traffic between driver and workers.

---

Providers: ADLS Ingestion to Bronze to Silver

1. Upload providers.tsv to the ADLS Gen2 container raw, under the path providers/providers.tsv. This is directly 
   accessible by the Databricks workspace via managed identity.

2. Run 01_bronze_stream_providers_autoloader.ipynb to ingest provider TSVs into kardia_bronze.bronze_providers using 
   Auto Loader with ABFS path access and managed identity authentication.

3. Run 01_validate_bronze_providers.ipynb to run basic assertions on the Bronze Providers table. This is non-blocking and will not fail the pipeline if issues are found.

4. Run 02_silver_providers_transform.ipynb to batch read from Bronze, apply SCD Type 2 logic, and write deduplicated rows to kardia_silver.silver_providers.


Claims: DBFS to Bronze to Silver

1. Run 99_bootstrap_raw_dirs_and_files.ipynb to copy the uploaded claims_10.avro file into the Auto Loader watch directory at dbfs:/kardia/raw/claims/.

2. Run 01_bronze_stream_claims_autoloader.ipynb to ingest claim Avro files into kardia_bronze.bronze_claims using Auto Loader and a predefined schema.

3. Run 01_validate_bronze_claims.ipynb to run basic assertions on the Bronze Claims table. This is non-blocking and will not fail the pipeline if issues are found.

4. Run 02_silver_claims_transform.ipynb to batch read Bronze claims, apply SCD Type 1 logic, and write cleansed data into kardia_silver.silver_claims.


Silver Join: Claims and Providers

- Run 02_silver_claims_enriched_join.ipynb to batch join Silver claims with provider details and write enriched results to kardia_silver.silver_claims_enriched.


Gold: Hourly Metrics and Provider Spend

- Run 03_gold_claims_metrics.ipynb to compute hourly claim volume and 7-day rolling spend metrics.
