# Providers, Claims & Feedback Ingestion

This pipeline ingests provider metadata, synthetic health claims, and patient feedback into a Databricks Lakehouse using Delta Lake. All datasets land in a Bronze layer with Change Data Feed (CDF) enabled, are validated, then transformed into Silver and Gold layers for analytics.

---

## Raw Bootstrap

Test files must first be manually uploaded to:
- `dbfs:/FileStore/tables/`

Then, run the appropriate bootstrap notebook to move them into raw ingestion zones:

- Claims → `dbfs:/kardia/raw/claims/claims_part_*.parquet`
- Providers → `dbfs:/kardia/raw/providers/providers_part_*.avro`
- Feedback → `dbfs:/kardia/raw/feedback/feedback_part_*.jsonl`

Use the `99_bootstrap_raw_sources.ipynb` or `99_move_new_*_files_to_raw.ipynb` notebooks to prepare these files for ingestion.

---

## Bronze Ingestion

| Dataset   | Source     | Format | Loader         | Bronze Table                     |
|-----------|------------|--------|----------------|----------------------------------|
| Providers | ADLS Gen2  | TSV    | Auto Loader    | `kardia_bronze.bronze_providers` |
| Claims    | DBFS       | Parquet| Auto Loader    | `kardia_bronze.bronze_claims`    |
| Feedback  | ADLS Gen2  | JSONL  | COPY INTO      | `kardia_bronze.bronze_feedback`  |

Each ingestion notebook reads raw files, infers schema (or uses an explicit one), adds audit columns, and writes to a Bronze Delta table.

---

## Silver Transformation

| Dataset   | Logic     | Silver Table                      |
|-----------|-----------|-----------------------------------|
| Providers | SCD Type 1 | `kardia_silver.silver_providers`  |
| Claims    | SCD Type 2 | `kardia_silver.silver_claims`     |
| Feedback  | Append     | `kardia_silver.silver_feedback`   |

Join notebooks create enriched views:
- `silver_claims_enriched`: Claims + current provider attributes
- `silver_feedback_enriched`: Feedback + current provider attributes

---

## Gold KPIs

| Table                             | Description                                              |
|----------------------------------|----------------------------------------------------------|
| `gold_claim_anomalies`           | Approval rates, denials, high-cost procedures           |
| `gold_provider_rolling_spend`    | Daily spend and rolling 7-day KPIs                      |
| `gold_feedback_metrics`          | Satisfaction, tags, comment stats (no claim linkage)    |

---

## Validation

Each Bronze table has a corresponding validation notebook that performs null checks, uniqueness tests, and basic profiling. Results are logged to `kardia_validation.*_summary` tables.