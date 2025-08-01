# Gold Layer: Claims, Feedback & Providers

Aggregates and reshapes curated Silver data into KPI-ready tables for reporting, anomaly detection, and quality metrics. Each notebook computes focused outputs with snapshot overwrite logic for simplicity and reliability.

---

## Outputs by Domain

### Claims

| Table Name                   | Description                                         |
|-----------------------------|-----------------------------------------------------|
| `gold_claim_approval_by_specialty` | Claim approval rates by provider specialty        |
| `gold_claim_denial_breakdown` | Denied claims broken down by diagnosis + specialty|
| `gold_high_cost_procedures`   | Top 10 procedures by average claim amount         |
| `gold_rapid_fire_claims`      | Patients filing >5 claims in a single day         |

Source: `silver_claims_enriched`  
Trigger: Snapshot overwrite (`CREATE OR REPLACE`)

---

### Feedback

| Table Name                      | Description                                               |
|--------------------------------|-----------------------------------------------------------|
| `gold_feedback_satisfaction`   | Scores, comment stats, and variability by specialty/source|
| `gold_feedback_tag_analysis`   | Tag frequency and average satisfaction per tag           |
| `gold_feedback_encounter_match`| % of feedback linked to valid encounter IDs              |

Source: `silver_feedback_enriched`  
Trigger: Snapshot overwrite

---

### Providers

| Table Name                  | Description                                      |
|----------------------------|--------------------------------------------------|
| `gold_provider_daily_spend`| Daily claim-based spend per provider             |
| `gold_provider_7d_spend`   | 7-day rolling spend and average using window ops |

Source: `silver_claims_enriched`  
Trigger: Snapshot overwrite