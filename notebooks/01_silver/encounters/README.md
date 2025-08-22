# Silver Layer: Patients & Encounters

Transforms Bronze records into clean, queryable Silver Delta tables using CDC logic (SCD‑1), PHI masking, and enrichment joins.  

Encounters tables support both batch and streaming modes, controlled via a `mode` parameter.

For field definitions and entity relationships, see the 
[Data Dictionary](../docs/data_dictionary.md) and [Source Schema](../docs/source_schema.md).

---

## Silver Tables

| Table Name                    | Description                                                       |
|------------------------------|-------------------------------------------------------------------|
| `silver_patients`              | Latest non-PHI demographics with birth year and masked identifiers |
| `silver_encounters`            | Deduplicated, timestamped clinical events with CDF-based updates   |
| `silver_encounters_enriched`   | Stream–static join of encounters with patient demographics |

---

## Patients

- Trigger: One-shot incremental batch from Bronze CDF
- Pattern: Deduplicate by `_commit_version`, mask PHI fields, derive `birth_year`
- Join Logic: Static dimension; used for enriching encounter streams

---

## Encounters

- Trigger: `mode=batch` drains and exits; `mode=stream` runs continuous 30s micro-batches
- Pattern: Upsert via MERGE using streaming `foreachBatch`
- Enrichment: Left join with silver_patients to produce `silver_encounters_enriched`

---

## Privacy Handling

The silver_patients table masks sensitive fields:

`first`, `last`, `ssn`, `drivers`, `passport`, `birthplace`, `address`, `prefix`, `suffix`, `maiden`

These columns are explicitly nulled at write time to prevent exposure.

---

## Output Format

External Delta tables in ADLS