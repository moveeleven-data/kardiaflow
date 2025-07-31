# Kardiaflow: Azure-Based Healthcare Data Pipeline

## Scenario

Kardiaflow simulates a real-world healthcare data pipeline built on Azure Databricks and Delta Lake. It demonstrates a 
modular, streaming-capable ETL architecture that handles structured (CSV, Avro, TSV) and semi-structured (JSON) healthcare datasets using a medallion design pattern.

The pipeline ingests raw files into Bronze Delta tables using Auto Loader, applies data masking and CDC logic in the Silver layer with Delta Change Data Feed (CDF), and materializes analytics-ready Gold views for reporting and dashboards.



## Architecture Overview

The following diagram illustrates the end-to-end data flow, including ingestion, transformation, validation, and storage layers:

![Kardiaflow Architecture](https://raw.githubusercontent.com/matthewtripodi-data/Kardiaflow/master/docs/assets/kflow_lineage.png?v=2)


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

---

## 🎥 Video Walkthrough: See Kardiaflow in Action

Want to see Kardiaflow in action? This end-to-end video walkthrough shows how data flows through each medallion layer and into dashboards powered by Gold tables.

📺 **Click to Watch on YouTube:**  
<a href="https://youtu.be/NrAe37O4QSM" target="_blank">
  <img src="https://img.youtube.com/vi/VBNmNdyTt7U/hqdefault.jpg" alt="Watch the demo on YouTube">
</a>

> **In this demo:**  
> • Lakeflow DAG execution (batch mode)  
> • Gold table refresh and validation  
> • Dashboard exploration (KPI views)  
> • QA and business metrics tabs  
>  
> *Streaming mode is supported but not shown here.*

---

## Setting Up the Infrastructure

Deploy the full Azure environment via:

🔗 [`infra/README.md`](infra/README.md) — *Infrastructure Deployment Guide*


> **Note:** KardiaFlow’s infrastructure is deployed manually via CLI.  
> Since environments are spun up for testing and torn down frequently, CI/CD automation is unnecessary.  
> The deployment remains reproducible through versioned scripts and configuration.

---

## Job Orchestration & Dashboards

This repo includes JSON definitions for batch job creation, job reset, and dashboard import via the Databricks CLI.

📂 [`pipelines/`](pipelines/) — *Databricks Jobs + Dashboards*

> No secrets are embedded in these files. See the folder's [README](pipelines/README.md) for full usage.

---

## Databricks Summit 2025: How It Shaped Kardiaflow

In June 2025, I completed 24 hours of hands-on training across six advanced data engineering workshops at the 
Databricks Data + AI Summit. These sessions directly influenced Kardiaflow’s design especially in areas like streaming pipeline robustness, CDC with Lakeflow Declarative Pipelines, data governance via Unity Catalog, and job orchestration with Lakeflow Jobs.

You can read my full reflection on the summit and how each session impacted Kardiaflow’s architecture here:  

👉 [`docs/summit_reflections.md`](docs/summit_reflections.md)

---

![CI](https://github.com/moveeleven-data/kardiaflow/actions/workflows/ci.yml/badge.svg)
