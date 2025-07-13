Providers & Claims Ingestion

This pipeline ingests two datasets into the Bronze layer of a Databricks Lakehouse:
provider metadata (via Postgres) and synthetic health claims (via Avro files and
Auto Loader). A single-node Postgres instance is installed in driver RAM at cluster
startup via an init script and configured using Databricks secrets. The database
is fully ephemeral—if the cluster auto-terminates, the driver VM (and with it, all
Postgres binaries, data, and tables) is wiped and reinitialized on the next start.

The Postgres password is stored in a Databricks secret scope (kardia) and injected
into the init script at runtime using an environment variable.

Providers: JDBC Ingestion

Before cluster creation:

1. Run the following CLI commands once per workspace to set up secure secrets.

databricks secrets create-scope --scope kardia
databricks secrets put --scope kardia --key pg_pw
# Enter demo123 when prompted (or any password)

2. Start the cluster without any init script or environment variables.

3. Run `99_bootstrap_raw_dirs_and_files.ipynb`. This creates the raw input
directory and verifies that providers_10.csv and claims_10.avro are uploaded to
/FileStore/tables/. It also copies the Avro file into the streaming watch folder.

4. Edit the cluster settings. Attach the start_postgres.sh init script. Set the
environment variable POSTGRES_PW={{secrets/kardia/pg_pw}}.

5. Restart the cluster. This installs and starts PostgreSQL inside the driver
and sets the postgres password using the resolved secret value.

6. Run `00_seed_providers_postgres.ipynb`. Waits for PostgreSQL to come online, 
loads providers_10.csv into Spark, and writes to a providers table in the embedded
Postgres database. Reads password via dbutils.secrets.get("kardia", "pg_pw").

7. Run `01_bronze_jdbc_providers.ipynb`. Reads the providers table via JDBC and
appends to kardia_bronze.bronze_providers.

Claims: Streaming Ingestion

1. Bootstrap: The same 99_bootstrap_raw_dirs_and_files.ipynb notebook copies the uploaded claims_10.avro file into the Auto Loader watch directory at dbfs:/kardia/raw/claims/.

2. Run 01_bronze_stream_claims_autoloader.ipynb. This defines the Avro schema in
code, creates the target Delta table, and performs a one-shot Auto Loader ingest.