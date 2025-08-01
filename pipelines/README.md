## Pipelines

Orchestration and visualization assets for **KardiaFlow**. This folder enables full demo runs, streaming ingestion, and job scheduling without modifying notebooks.

### Contents

- `jobs/`
  - `kardiaflow_full_run_batch.json` – creates the full batch demo job (runs all domains end-to-end with `mode=batch`)
  - `reset_kardiaflow_full_run_batch.json` – resets the full job in place (idempotent)
  - `kardiaflow_encounters.json` – standalone encounters pipeline (supports batch or streaming via `mode` parameter)
  - `kardiaflow_patients_batch.json` – scheduled batch job for refreshing silver patients table
- `dashboards/`
  - `Kardiaflow Analytics.lvdash.json` – Databricks SQL dashboard export

> Tasks and dependencies are defined in the job JSON. The data flow follows:  
> **Raw → Bronze → Silver → Gold → Validation**

---

### Prerequisites

- Databricks CLI configured (`databricks configure --profile kardia`)  
  See `infra/README.md` for setup.
- `kflow` wheel uploaded to `dbfs:/Shared/libs`  
  See `infra/README.md` for build and upload steps.

---

### Create the Jobs

```bash
# Full demo job
databricks jobs create \
  --json @pipelines/jobs/kardiaflow_full_run_batch.json \
  --profile kardia
```

```bash
# Encounters (toggleable streaming)
databricks jobs create \
  --json @pipelines/jobs/kardiaflow_encounters.json \
  --profile kardia
```

```bash
# Patients batch
databricks jobs create \
  --json @pipelines/jobs/kardiaflow_patients_batch.json \
  --profile kardia
```

---

### Reset the Job

```bash
databricks jobs reset \
  --json @pipelines/jobs/reset_kardiaflow_full_run_batch.json \
  --profile kardia
```

### Run the Demo

```bash
databricks jobs run-now --job-id <JOB_ID> --profile kardia
```

**Encounters mode parameter**

The Encounters pipeline accepts a mode parameter:

- batch: run once and exit
- stream: 30s micro-batches (long-running)

This can be set in the UI or modified directly in the job JSON (base_parameters).

### What the Job Does

- Bronze: raw → Bronze via Auto Loader
- Silver: deduplication, PHI masking, SCD (1/2), joins
- Gold: analytics views and tables
- Validation: smoke tests logged to kardia_validation.smoke_results

(Details in notebooks/README.md.)

---

### Dashboard Import

To import the dashboard, use the Databricks UI:

**Dashboards → Import → Kardiaflow Analytics.lvdash.json**

---

**NOTE:**

- Job/dashboard JSONs contain no secrets
- Auth handled via Databricks CLI profile + secret scopes