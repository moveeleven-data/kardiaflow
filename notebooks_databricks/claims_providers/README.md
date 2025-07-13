Providers & Claims Ingestion

This pipeline sets up and ingests two datasets into the Bronze layer of a Databricks Lakehouse: provider metadata (via Postgres) and synthetic health claims (via Avro files and Auto Loader). We use a single-node Postgres instance started by a cluster init script that runs in driver RAM. The embedded Postgres database persists across cluster termination.

The Postgres password is kept out of Git and notebooks, stored in DBFS in a plaintext file.

Providers: JDBC Ingestion

1. Start the cluster without any init script or environment variables.

2. Run 99_bootstrap_raw_dirs_and_files.ipynb. This will create the raw input directory, verify that providers_10.csv is uploaded to /FileStore/tables/, and save the PostgreSQL password (demo123) to DBFS at /secrets/pg_pw.

3. Edit the cluster settings to attach the start_postgres.sh init script and set the environment variable POSTGRES_PW=demo123, then restart the cluster. This installs and configures PostgreSQL inside the driver using the password.

4. Run 00_seed_providers_postgres.ipynb to wait for PostgreSQL to come online, load providers_10.csv into Spark, and overwrite the providers table in Postgres.

5. Run 01_bronze_jdbc_providers.ipynb to read the providers table via JDBC and write to kardia_bronze.bronze_providers.

Claims: Streaming Ingestion

1. Bootstrap: The same bootstrap notebook also copies the uploaded claims_10.avro file into the Auto Loader watch directory dbfs:/kardia/raw/claims/.

2. Bronze Ingest: The 01_bronze_stream_claims_autoloader.ipynb notebook defines the Avro schema in code, creates the target Delta table, and runs a one-shot Auto Loader streaming job using availableNow=true. The .option("mergeSchema", "true") setting allows schema evolution from initial data.