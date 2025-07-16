Providers & Claims Ingestion

This pipeline ingests two datasets into the Bronze layer of a Databricks Lakehouse:
provider metadata (via Postgres) and synthetic health claims (via Avro files and
Auto Loader). A single-node Postgres instance is installed in driver RAM at cluster
startup via an init script and configured using Databricks secrets. The database
is fully ephemeral—if the cluster auto-terminates, the driver VM (and with it, all
Postgres binaries, data, and tables) is wiped and reinitialized on the next start.

NOTE: All source files and every Delta table are stored in DBFS object storage which is
encrypted at rest automatically. Reads and writes between the cluster and that object
store travel over TLS-encrypted HTTPS, so those stages are also encrypted in transit.
Inside the cluster, two paths remain unencrypted: Spark shuffle/broadcast traffic between
driver and workers and the JDBC connection to the temporary Postgres instance on the
driver node (plain TCP on localhost).

In Production, I would connect to a managed Postgres instance (Azure Database, RDS)
over VNet with TLS enforced. The cloud provider provides the certificate and credentials
come from Azure Key Vault/Secrets Manger. The database would already be encrypted
at rest with Transparent Data Encryption (TDE).

The Postgres password is stored in a Databricks secret scope (kardia) and injected
into the init script at runtime using an environment variable.

---

Providers: JDBC Ingestion

Before cluster creation:

1. In local dev environment, run the following CLI commands to set up secure secrets:

Replace Workspace URL with current Workspace URL.

databricks auth login \
  --host https://adb-1962984722680540.0.azuredatabricks.net \
  --profile adb-1962984722680540

databricks secrets create-scope kardia --initial-manage-principal "users" --profile adb-1962984722680540
databricks secrets put-secret kardia pg_pw --string-value demo123 --profile adb-1962984722680540

2. Edit the cluster settings. Attach the start_postgres.sh init script in the
utilies folder. Set the environment variable POSTGRES_PW={{secrets/kardia/pg_pw}}.
Restart the cluster. This installs and starts PostgreSQL inside the driver and
sets the postgres password using the resolved secret value.

3. Ensure the test files were added to DBFS and run `99_bootstrap_raw_dirs_and_files.ipynb`.
This creates the raw input directory and verifies that providers_10.csv and
claims_10.avro are uploaded to /FileStore/tables/. It also copies the Avro
file into the streaming watch folder.

4. Run `99_seed_providers_postgres.ipynb`. Waits for PostgreSQL to come online, 
loads providers_10.csv into Spark, and writes to a providers table in the embedded
Postgres database. Reads password via dbutils.secrets.get("kardia", "pg_pw").

5. Run `01_bronze_jdbc_providers.ipynb`. Reads the providers table via JDBC and
appends to kardia_bronze.bronze_providers.

Claims: Incremental Batch Ingestion

1. Bootstrap: The same 99_bootstrap_raw_dirs_and_files.ipynb notebook copies the
uploaded claims_10.avro file into the Auto Loader watch directory at dbfs:/kardia/raw/claims/.

2. Run 01_bronze_stream_claims_autoloader.ipynb. This defines the Avro schema in
code, creates the target Delta table, and performs a one-shot Auto Loader ingest.