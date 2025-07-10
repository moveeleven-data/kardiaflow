# KardiaFlow: Azure-Based Healthcare Data Platform

## Scenario

KardiaFlow simulates a modern healthcare data engineering platform built entirely on Azure and Databricks. It emulates a hospital network integrating diverse data sources — from patient demographics and claims to IoT vitals and feedback — using a production-style streaming pipeline.

The project covers end-to-end ingestion, transformation, change data capture, data modeling, masking of PHI, and dashboard-ready Gold views, all within a scalable, cloud-native Lakehouse architecture. It showcases streaming Auto Loader ingestion, Delta Lake medallion layers (Bronze/Silver/Gold), Delta CDF, automated data validation, and SQL-based KPIs designed for healthcare analytics.

### Architecture Overview

This high-level diagram shows how structured and semi-structured healthcare data flows from ingestion to transformation, validation, and secure storage using Azure-native tools.

![KardiaFlow Architecture](https://github.com/okv627/KardiaFlow/raw/kardiaflow-v1/docs/assets/kardiaflow_lineage.png)

### Data Sources

- **EHR Data (Structured, Simulated)** — CSV exports emulating Oracle or SQL Server sources:
  - `patients.csv`  : demographic and ID information
  - `encounters.csv`: hospital visit metadata

- **Insurance Claims Data (Structured, Simulated)** — CSV files representing PostgreSQL-style claims and provider records:
  - `claims.csv`: claim cost, provider, coverage, billing codes
  - `providers.csv`: metadata about insurers and medical providers

- **Patient Feedback & Device Logs (Semi-Structured, Simulated)** — JSON files imitating MongoDB-style documents:
  - `feedback.json`: patient satisfaction surveys
  - `device_data.json`: wearable health metrics (e.g., heart rate, step count)

---

## Goals

- **Streaming ingestion** of structured and semi-structured healthcare data using **Databricks Auto Loader**, with safe schema evolution, timestamp tracing, and incremental file detection from simulated source folders
- **Bronze Delta Lake landing tables** for each data feed (patients, encounters, claims, procedures, providers, feedback, IoT devices), capturing ingest-time metadata for lineage and debug visibility
- **Change Data Feed (CDF)** enablement across Bronze layers to track inserts and updates for downstream deduplication, merge logic, and CDC-style transformations
- **Silver layer modeling** with PII masking, deduplication, schema enforcement, windowed aggregates, and normalized join patterns — including SCD logic and wide-table patient encounter joins
- **Gold layer materialization** of business-facing analytics views (e.g., gender breakdown, encounters by month, rolling claim totals, patient vitals) optimized for dashboards and reporting
- **Data quality enforcement** using PySpark assertions and expectations to validate masking, uniqueness, and domain constraints at each stage
- **Environment toggling and portability** across local dev and Azure Databricks using modular path configuration logic and automated teardown protocols to reduce cloud spend
- **Lightweight observability** with row counts, freshness tracking, and test coverage across key layers
- **Databricks SQL dashboards** for visualization of KPIs with rolling time trends and categorical breakdowns
- **CI-friendly notebook structure** with modular stages (validation, Bronze, Silver, Gold), enabling future expansion into dbt, real-time alerts, or warehouse sync

---

## Tech Stack

| Layer           | Tools / Services                                                                 |
|------------------|----------------------------------------------------------------------------------|
| **Cloud Platform** | Azure (Databricks, Key Vault, Storage, Resource Groups)                        |
| **Ingestion**      | Databricks Auto Loader (streaming CSV + JSON)                                 |
| **Data Lake**       | Delta Lake (Bronze, Silver, Gold layers with CDF enabled)                     |
| **Compute Engine**  | Apache Spark (PySpark) on Azure Databricks (single-node and cluster mode)     |
| **Workflow Logic**  | Modular Databricks notebooks, Spark SQL, Python utilities                     |
| **Validation**      | PyTest, Spark DataFrame assertions, row count and domain checks               |
| **Governance**      | Deterministic PHI masking, schema enforcement, CDF version tracking           |
| **Analytics & BI**  | Databricks SQL dashboards, Gold views, aggregations, KPI visualizations       |
| **Dev & Automation**| GitHub, Python virtualenv, local CLI (spark-submit), teardown scripts         |
| **Portability**     | Environment toggling (local vs Databricks) via config utility `cfg()`         |
| **Observability**   | Lightweight row counts, freshness tracking, log outputs in notebooks           |

---

## Compliance Focus

This project simulates responsible healthcare data practices by incorporating:

- **Simulated HIPAA Security Rule adherence**, especially regarding ePHI
- **PHI identification and masking** for fields like name, birthdate, and medical record number
- **Security best practices**, such as separation of secrets, encryption in transit, and audit logging
- **Data governance artifacts**, including data lineage diagrams, update frequency, and ownership tracking

---

## Branches

- [`master`](https://github.com/okv627/KardiaFlow/tree/master): Full commit history showing development process
- [`kardiaflow-v1`](https://github.com/okv627/KardiaFlow/tree/kardiaflow-v1): Clean, single-commit release version for portfolio review

