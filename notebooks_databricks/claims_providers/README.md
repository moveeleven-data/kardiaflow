Providers & Claims Ingestion

This pipeline ingests two datasets into the Bronze layer of a Databricks Lakehouse:
provider metadata (via CSV files in ADLS Gen2 and Auto Loader) and synthetic health
claims (via Avro files and Auto Loader). The provider data now resides in the raw
container of an Azure Data Lake Storage Gen2 account, and Auto Loader ingests it
directly using the Databricks workspace's managed identity, with no secrets or SAS
tokens required. This fully replaces the previous approach, which used a single-node
Postgres instance installed in driver RAM via an init script.

NOTE: All source files and every Delta table are stored in DBFS object storage,
which is encrypted at rest automatically. Reads and writes between the cluster
and that object store travel over TLS-encrypted HTTPS, so those stages are also
encrypted in transit. Inside the cluster, one path remains unencrypted: Spark
shuffle/broadcast traffic between driver and workers.

In production, I would still connect sensitive transactional sources (like
operational Postgres or SQL Server instances) via a managed service (Azure
Database, RDS) over a VNet with TLS enforced. The cloud provider would supply
the certificate, credentials would come from Azure Key Vault or Secrets Manager,
and the database would be encrypted at rest with Transparent Data Encryption (TDE).

The current demo flow for Providers uses ADLS with MSI authentication; no init
scripts or secrets are required for this path.

---

Providers: ADLS Ingestion

1. Upload `providers.csv` to the ADLS Gen2 container raw, under the path:
`providers/providers.csv`.

2. Run `01_bronze_providers_adls_msi.ipynb`. Auto Loader will read all CSV files under
`abfss://raw@<storage-account>.dfs.core.windows.net/providers/` and append rows into
the `kardia_bronze.bronze_providers` Delta table (CDF enabled).

NOTE: Authentication uses the Databricks workspace managed identity. No secrets
or SAS tokens are required.

Claims: Incremental Batch Ingestion

1. Bootstrap: The same `99_bootstrap_raw_dirs_and_files.ipynb` notebook copies the
uploaded `claims_10.avro` file into the Auto Loader watch directory at `dbfs:/kardia/raw/claims/`.

2. Run `01_bronze_stream_claims_autoloader.ipynb`. This defines the Avro schema in
code, creates the target Delta table, and performs a one-shot Auto Loader ingest.