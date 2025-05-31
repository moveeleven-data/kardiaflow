# KardiaFlow Project — Changelog

## 2025-05-30

Today focused on the ingestion and validation of the synthetic EHR patient dataset into Oracle XE. We developed and finalized a robust Python script (`load_patients.py`) to batch load `patients.csv` from `data/raw/ehr/` into the `patients` table within the Oracle database. The script utilizes **pandas** for high-throughput data wrangling and **cx_Oracle** for database interaction.

Critical data quality safeguards were implemented within the pipeline:

- **Primary key enforcement**: Rows with missing or null `ID` values are skipped.
- **Deduplication logic**: Previously inserted patients are excluded by checking against existing Oracle records.
- **Field length validation**: Fields such as `SUFFIX`, `GENDER`, and `SSN` are trimmed to Oracle-safe lengths to avoid `ORA-12899` errors.
- **Date coercion**: Invalid or malformed dates are gracefully nullified using `pandas.to_datetime`, preserving otherwise valid records.
- **Error resilience**: Failed inserts are caught individually and logged to `logs/skipped_patients.csv` for review.

Performance-wise, the script successfully ingested over **133,000** patient records while skipping a small subset (~72 rows) due to data violations—these were logged for future inspection.

To support clean version control, the `.gitignore` was updated to exclude the `logs/` directory and generated CSVs containing insert failures. This allows the repository to remain clean while preserving transparency in load operations.

This ingestion layer forms a crucial link in the overall KardiaFlow architecture, bridging raw EHR exports with downstream analytics and validation pipelines.

---

## 2025-05-29

Today marked the foundational setup of the KardiaFlow project’s infrastructure and datasets. An Azure account was created and provisioned with both **Azure Data Factory** and **Azure Databricks**, using the East US region to avoid quota limitations. These services will form the backbone of our orchestration and transformation layers.

Simultaneously, the local development environment was established using Docker containers for **PostgreSQL**, **MongoDB**, **Oracle XE**, and **SQL Server**. Each of these databases was configured to simulate realistic hybrid healthcare systems, and connection scripts were written in Python to validate access to all services. These scripts were organized under `automation/db_checks/`, and results were logged to `docs/environment_check.md`.

On the Python side, a virtual environment was created using `venv`, and essential packages such as `pyspark`, `pandas`, `sqlalchemy`, and `pymongo` were installed. This environment will support local testing, data generation, and PySpark-based transformations.

The raw data layer was also initialized. We sourced a synthetic health insurance claims dataset from Kaggle and placed the files—`claims.csv` and `providers.csv`—under `data/raw/claims/`. Two additional JSON files, `feedback.json` and `device_data.json`, were custom generated to simulate semi-structured patient feedback and wearable device data. These were saved under `data/raw/feedback/`.

Separately, a large synthetic EHR dataset was generated using **Synthea**. After extracting twelve `.tar.gz` archives into a consolidated output directory, we curated and moved core CSVs (`patients.csv`, `encounters.csv`, and `procedures.csv`) into the `data/raw/ehr/` directory. The rest of the archive was excluded from version control via `.gitignore`.

Finally, the project was initialized as a Git repository and connected to GitHub. A clean `.gitignore` was configured to prevent large datasets, environments, and cache files from polluting the repository. All datasets and environments were documented in `data/data_dictionary.md`, covering both schema definitions and usage notes for claims, feedback, device data, and EHR records.
