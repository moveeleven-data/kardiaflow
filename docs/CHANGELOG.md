# KardiaFlow Project — Changelog

## 2025-06-23

Raw → Gold View Pipeline Complete

Today we finalized the KardiaFlow architecture, integrating batch and streaming
PHI-compliant ETL paths and clarifying ingestion options like Auto Loader and
COPY INTO. We validated a raw 100-row CSV, ingested it into a Bronze Delta
table with Change Data Feed enabled, then transformed it to a schema-enforced,
masked Silver layer. Unit tests confirmed data quality (masking, enum
correctness, uniqueness), and we capped the workflow by creating a Gold-layer
KPI view (`vw_gender_breakdown`) using Delta SQL over a temp view. The pipeline
runs seamlessly in both local and Databricks environments.

This marks completion of a full-stack mini pipeline — raw → Bronze → Silver → Gold
— complete with Delta features, unit tests, and production-ready KPIs.


## 2025-06-22

Completed Phase 1 and began Phase 2 of KardiaFlow by deploying safe,
cost-controlled infrastructure and validating an initial data pipeline run.
Used `deploy.bicep` to provision Azure Databricks (public-only, no VNet),
Key Vault (soft-delete enabled, purge protection off), and Azure Data Factory.
Confirmed no NAT Gateways or other hidden costs. Created a $5/month
Azure Budget Alert to prevent overages.

Built and verified a full infra loop with `az group create`,
`az deployment group create`, and `automation/infra/teardown.sh`, ensuring
clean teardown and full idempotence. Launched a minimal 1-node Databricks
cluster (Standard_D4s_v3, 10-min auto-terminate), and uploaded `patients_1k.csv`
to DBFS via CLI.

Created and executed the `00_mask_transform_validate` notebook, reading the
file with minimal schema inference, previewing rows, and writing a small Delta
table (`kardia_patients_stage`) with a load timestamp. Verified Spark plan and
partition count to ensure cost-efficiency.

Linked the Databricks workspace to GitHub via Repos, committed the notebook,
and pulled changes locally in PyCharm. All steps support reproducibility,
fast iteration, and teardown-safe development.

## 2025-06-04

After uncovering substantial and silently accumulating costs tied to ADLS Gen2
transaction billing, NAT Gateway persistence, and unremovable infrastructure
triggered by Unity Catalog's Access Connector, the KardiaFlow environment
(`kardiaflow-rg`) was systematically dismantled. Despite having Owner-level
permissions, key resources remained locked behind deny assignments automatically
applied during Unity Catalog provisioning. This prevented deletion of the
NAT Gateway, public IPs, and associated networking components. The situation
was resolved only after escalating to Microsoft Support, who manually removed
the deny policies. With that, all residual services—including Databricks-managed
identities, virtual networks, and the storage account holding partitioned
Parquet output—were eliminated, halting all further billing.

With the environment now fully reset, the project enters a structured four-day
simulation phase grounded in hardened cloud hygiene. The new protocol emphasizes
transient infrastructure by creating and deleting a dedicated resource group daily,
avoiding external storage, and limiting all transformation outputs to `/dbfs/tmp/`.
Over the next four days, I will sequentially explore safe implementations of
streaming ingestion (via Spark’s rate source), star schema modeling and serverless
SQL, Great Expectations for data quality, and Unity Catalog through offline
simulation or short-lived, controlled sessions. This phase will prioritize
operational reversibility and explicit cost boundaries, instilling best practices
for cloud-native data engineering without risk of recurrence.

## 2025-06-03

Developed and tested Azure Data Factory (ADF) copy pipelines to move data from
multiple source systems (Oracle, PostgreSQL, MongoDB) into raw landing zones in
Azure Data Lake Storage (ADLS Gen2). Utilized the Copy Activity in ADF to
extract data as Parquet/CSV and load it into the cloud, organizing pipelines
by source. Verified data ingestion through ADF execution and monitoring, ensuring
successful data landing and row count matching. Set up logging and notifications
for success and failure events.

Added a data validation layer to ensure successful data loading by
cross-checking row counts and performing basic data validation. Used the ADF
Monitor to track pipeline progress and verify completeness of the ingested data.

Set up Databricks and PySpark for data transformation. Mounted Azure Data Lake
Storage (ADLS Gen2) to DBFS and successfully loaded Parquet files into Databricks
notebooks. Performed initial exploration of the data by displaying schemas and
previewing the first few rows of the patients, encounters, and procedures datasets.
Verified successful loading and examined the structure to prepare for subsequent
data transformations.

Set up an Azure Databricks workspace and cluster for data transformation using
PySpark. Loaded raw data from Azure Data Lake Storage (ADLS Gen2) into Databricks,
reading Parquet files into Spark DataFrames and performing initial schema
exploration. Transformed the data by renaming columns, joining patient records
with encounter and procedure data, handling missing values, and adding new
fields like encounter count and readmission flags. Repartitioned the DataFrame
for efficient parallel processing and wrote the cleaned data to ADLS Gen2 in
Parquet format, partitioned by `final_patient_ID` and `encounter_DATE`. Verified
data output by successfully writing 5000 rows, ensuring data quality and
preparing for future processing steps.

## Changelog – 2025-06-02

- Set up and tested all data connections needed for Azure Data Factory to move
  data between systems.
- Created and connected to:
  - A local Oracle XE database
  - A local PostgreSQL database (on port 5433)
  - A local MongoDB instance
  - A cloud-based Azure Data Lake Storage (ADLS Gen2) account named
    `kardiaflowstorage`
- Used a self-hosted integration runtime (SHIR) to securely connect local
  databases to Azure.
- Stored all passwords and access keys in Azure Key Vault (`kardiaflow-kv`)
  for security.
- Verified that all connections worked by running tests in the ADF user interface.

## 2025-06-01

Resolved Oracle XE ingestion failures on `encounters.csv` (~1.5M rows) due to
index space exhaustion in the default `SYSTEM` tablespace. Created a dedicated
`USERS_DATA` tablespace for user data and updated `load_encounters.py` to
support mid-batch commits, `executemany()`, and retry logging via
`logs/skipped_encounters.csv`. Final run completed with no skipped rows. Also
ingested `procedures.csv` (624,139 rows, 0 skips).

Stood up a new PostgreSQL container (`postgres:15` on port 5433), created the
`claims` database, and developed ingestion scripts for `claims.csv` and
`providers.csv`. Scripts include snake_case normalization, deduplication on
primary keys, and schema alignment. Successfully loaded 4,500 claims and
1,500 providers.

Deployed MongoDB (`mongo:7` on port 27017) and created the `healthcare`
database. Wrote an ingestion script for `feedback.json` that parses timestamps,
cleans text fields, and inserts into the `feedback` collection. All 50 documents
loaded successfully.

Finally, created a validation notebook (`source_validation_checks.ipynb`)
to confirm ingestion integrity across all systems. Ran cross-database row
counts, sampled data, and checked for anomalies in `patients`, `claims`,
and `feedback`. All counts and structures verified.

---

## 2025-05-30

Today focused on the ingestion and validation of the synthetic EHR patient
dataset into Oracle XE. I developed and finalized a robust Python script
(`load_patients.py`) to batch load `patients.csv` from `data/raw/ehr/` into
the `patients` table within the Oracle database. The script utilizes **pandas**
for high-throughput data wrangling and **cx_Oracle** for database interaction.

Critical data quality safeguards were implemented within the pipeline:

- **Primary key enforcement**: Rows with missing or null `ID` values are skipped.
- **Deduplication logic**: Previously inserted patients are excluded by checking against existing Oracle records.
- **Field length validation**: Fields such as `SUFFIX`, `GENDER`, and `SSN` are trimmed to Oracle-safe lengths to avoid `ORA-12899` errors.
- **Date coercion**: Invalid or malformed dates are nullified using `pandas.to_datetime`, preserving otherwise valid records.
- **Error resilience**: Failed inserts are caught individually and logged to `logs/skipped_patients.csv` for review.

Performance-wise, the script successfully ingested over **133,000** patient records while skipping a small subset (~72 rows) due to data violations—these were logged for future inspection.

---

## 2025-05-29

Today marked the foundational setup of the KardiaFlow project’s infrastructure and datasets. An Azure account was created and provisioned with both **Azure Data Factory** and **Azure Databricks**, using the East US region to avoid quota limitations. These services will form the backbone of our orchestration and transformation layers.

Simultaneously, the local development environment was established using Docker containers for **PostgreSQL**, **MongoDB**, **Oracle XE**, and **SQL Server**. Each of these databases was configured to simulate realistic hybrid healthcare systems, and connection scripts were written in Python to validate access to all services. These scripts were organized under `automation/db_checks/`, and results were logged to `docs/environment_check.md`.

On the Python side, a virtual environment was created using `venv`, and essential packages such as `pyspark`, `pandas`, `sqlalchemy`, and `pymongo` were installed. This environment will support local testing, data generation, and PySpark-based transformations.

The raw data layer was also initialized. We sourced a synthetic health insurance claims dataset from Kaggle and placed the files—`claims.csv` and `providers.csv`—under `data/raw/claims/`. Two additional JSON files, `feedback.json` and `device_data.json`, were custom generated to simulate semi-structured patient feedback and wearable device data. These were saved under `data/raw/feedback/`.

Separately, a large synthetic EHR dataset was generated using **Synthea**. After extracting twelve `.tar.gz` archives into a consolidated output directory, we curated and moved core CSVs (`patients.csv`, `encounters.csv`, and `procedures.csv`) into the `data/raw/ehr/` directory. The rest of the archive was excluded from version control via `.gitignore`.

Finally, the project was initialized as a Git repository and connected to GitHub. A clean `.gitignore` was configured to prevent large datasets, environments, and cache files from polluting the repository. All datasets and environments were documented in `data/data_dictionary.md`, covering both schema definitions and usage notes for claims, feedback, device data, and EHR records.
