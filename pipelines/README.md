## Pipelines

Orchestration and visualization assets for **KardiaFlow**. This folder enables full demo runs without modifying notebooks.

### Contents

- `jobs/`
  - `kardiaflow_full_run_batch.json` – creates the batch demo job
  - `reset_kardiaflow_full_run_batch.json` – resets the job in place (idempotent)
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

### Create the Job

```bash
databricks jobs create \
  --json @pipelines/jobs/kardiaflow_full_run_batch.json \
  --profile kardia
```

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

Some tasks accept a mode parameter:

- batch: run once and exit
- stream: 30s micro-batches (long-running)

Set in the UI or modify the job JSON.

### What the Job Does

- Bronze: raw → Bronze via Auto Loader
- Silver: deduplication, PHI masking, SCD (1/2), joins
- Gold: analytics views and tables
- Validation: smoke tests logged to kardia_validation.smoke_results

(Details in notebooks/README.md.)

---

To import the dashboard, use the Databricks UI: Dashboards → Import

NOTE:

- Job/dashboard JSONs contain no secrets
- Auth handled via Databricks CLI profile + secret scopes