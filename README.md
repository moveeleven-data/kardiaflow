# Kardiaflow: Azure-Based Healthcare Data Platform

## Scenario

Kardiaflow simulates a real-world healthcare data platform built on Azure Databricks and Delta Lake. It demonstrates a modular, streaming-capable ETL architecture that handles structured (CSV, Avro, TSV) and semi-structured (JSON) healthcare datasets using a medallion design pattern.

The pipeline ingests raw files into Bronze Delta tables using Auto Loader, applies data masking and CDC logic in the Silver layer with Delta Change Data Feed (CDF), and materializes analytics-ready Gold views for reporting and dashboards.



## Architecture Overview

The following diagram illustrates the end-to-end data flow, including ingestion, transformation, validation, and storage layers:

![Kardiaflow Architecture](https://raw.githubusercontent.com/okv627/Kardiaflow/master/docs/assets/kflow_lineage.png?v=2)



## Key Features

**Multi-Domain Simulation**  
&nbsp;&nbsp;&nbsp;&nbsp;• *Clinical*: Patients, Encounters  
&nbsp;&nbsp;&nbsp;&nbsp;• *Billing & Feedback*: Claims, Providers, Feedback

**Multi-Format Ingestion**  
&nbsp;&nbsp;&nbsp;&nbsp;• Structured formats (CSV, Avro, Parquet, TSV) via Auto Loader  
&nbsp;&nbsp;&nbsp;&nbsp;• Semi-structured JSONL via COPY INTO  
&nbsp;&nbsp;&nbsp;&nbsp;• All Bronze tables include `_ingest_ts`, `_source_file`, and enable Change Data Feed (CDF)  


**Privacy-Aware Transformations**  
&nbsp;&nbsp;&nbsp;&nbsp;• Deduplication, PHI masking, SCD Type 1/2  
&nbsp;&nbsp;&nbsp;&nbsp;• Supports streaming and batch upserts  


**Business-Ready Gold KPIs**  
&nbsp;&nbsp;&nbsp;&nbsp;• Lifecycle metrics, spend trends, claim anomalies, feedback sentiment  
&nbsp;&nbsp;&nbsp;&nbsp;• Materializes curated tables for analytics  


**Automated Data Validation**  
&nbsp;&nbsp;&nbsp;&nbsp;• `99_smoke_checks.py` tests row counts, nulls, duplicates, and schema contracts  
&nbsp;&nbsp;&nbsp;&nbsp;• Logs results to Delta for auditing and observability  


**Modular Notebook Design**  
&nbsp;&nbsp;&nbsp;&nbsp;• One notebook per dataset and medallion layer  
&nbsp;&nbsp;&nbsp;&nbsp;• Clean flow: Raw → Bronze → Silver → Gold  


**Reproducible Infrastructure-as-Code**  
&nbsp;&nbsp;&nbsp;&nbsp;• Declarative Bicep deployments via Azure CLI  
&nbsp;&nbsp;&nbsp;&nbsp;• Secrets managed via Databricks CLI  
&nbsp;&nbsp;&nbsp;&nbsp;• One-command teardown: `infra/teardown.sh`



## Setting Up the Infrastructure

Deploy the full Azure environment via:

[`infra/README.md`](infra/README.md) — *Infrastructure Deployment Guide*

> ⚠️ Commands must be run from the **project root**.



## Technology Stack

| Layer        | Tool/Service                  |
|--------------|-------------------------------|
| Cloud        | Azure                         |
| Storage      | ADLS Gen2                     |
| Compute      | Azure Databricks              |
| ETL Engine   | Spark Structured Streaming     |
| Metadata     | Delta Lake w/ CDF |
| Infra-as-Code| Bicep + Azure CLI             |
| Validation   | PySpark → Delta               |
