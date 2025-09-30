<h1 align="center">Kardiaflow: Azure Databricks Healthcare Lakehouse</h1>

<p align="center">
  Turn raw healthcare records into protected, analytics-ready data.
  <br/><br/>
</p>

<p align="center"><b>▷ See It in Action (2-min demo)</b></p>

<p align="center">
  <a href="https://youtu.be/YPaAU44Tdvw" target="_blank">
    <img src="https://img.youtube.com/vi/YPaAU44Tdvw/hqdefault.jpg" width="420" alt="Watch the demo on YouTube"/>
  </a>
</p>

---

## Key Features

| Capability | What you get                                             |
|---|----------------------------------------------------------|
| **Streaming** | Auto Loader for streams, COPY INTO for bulk |
| **Privacy**  | History-aware Silver via Delta MERGE/CDF               |
| **Analytics** | Gold KPIs for Databricks SQL (lifecycle, spend, sentiment) |
| **Quality** | Smoke checks written to audit table; unit tests via GitHub Actions |
| **IaC** | Bicep deploy/teardown, secrets in scopes, single-node friendly |



## Pipeline Architecture

![Kardiaflow Architecture](docs/assets/kflow_lineage_3.png)

<sup>Raw patient, encounter, claims, provider, and feedback data land in **Bronze**, **Silver** applies PHI masking and CDC, **Gold** aggregates metrics for analytics.</sup>



## Run It Yourself on Azure

Kardiaflow is fully reproducible on Azure with Bicep and CLI scripts. In ~5–10 minutes you’ll have a Databricks 
workspace, ADLS Gen2, and a service principal. A teardown script is included to avoid lingering costs.

**Prereqs:** Azure subscription, Azure CLI, Databricks CLI, Databricks PAT.

1) **Configure** - Copy `.env.example` → `.env` and fill in SUB/RG/etc.  
2) **Deploy** - Create RG and deploy Databricks + ADLS with Bicep (see `infra/README.md`).  
3) **Set up Databricks** - Authenticate CLI, create a Service Principal, publish the `kflow` wheel.  
4) **Run & clean up** - Bootstrap sample data, import the “full run” job, **Run now**, then tear down to avoid cost.

🔗 Full guide: [infra/README.md](infra/README.md)  
> **Note:** Runs on a single-node Databricks cluster for just a few dollars.



## Codebase Overview

**[notebooks/](notebooks/)** - End-to-end workflows across Bronze, Silver, and Gold layers.

  - Bronze example: [`bronze_patients_autoloader.ipynb`](notebooks/00_bronze/encounters/bronze_patients_autoloader.ipynb)  
  - Silver example: [`silver_patients_scd1_batch.ipynb`](notebooks/01_silver/encounters/silver_patients_scd1_batch.ipynb)

**[kflow/](kflow/)** - Core library with authentication, ETL utilities, and validation helpers.

**[pipelines/](pipelines/)** - Databricks job JSON definitions and dashboard exports.

**[infra/](infra/)** - Bicep templates and CLI scripts for reproducible deployment (see [infra/README.md](infra/README.md)). 

**[docs/](docs/)** - Reference materials, such as the [data_dictionary.md](docs/data_dictionary.md). 



## Databricks Summit 2025

Reflections from Databricks Summit workshops on streaming and governance:  [docs/summit_reflections.md](docs/summit_reflections.md).

---

<p align="center">
  <a href="https://github.com/moveeleven-data/kardiaflow/actions/workflows/ci.yml">
    <img src="https://github.com/moveeleven-data/kardiaflow/actions/workflows/ci.yml/badge.svg" alt="CI status"/>
  </a>
</p>
