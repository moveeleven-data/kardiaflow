# 00_config.py
# Configuration for KardiaFlow smoke tests:
# - Defines test status constants and run timestamp
# - Declares table-level test contracts for Bronze, Silver, and Gold layers
# - Controls duplicate suppression logic for primary key validation
from datetime import datetime

# -------------------------------------------------------------------------
# Status constants for test outcomes
# -------------------------------------------------------------------------
PASS = "PASS"
FAIL = "FAIL"
ERROR = "ERROR"

# -------------------------------------------------------------------------
# Results table location and current run timestamp
# -------------------------------------------------------------------------
RESULTS_TABLE = "kardia_validation.smoke_results"
RUN_TS = datetime.utcnow()  # Timestamp applied to all log records

# -------------------------------------------------------------------------
# Bronze-layer test contract: (table_name, primary_key)
# -------------------------------------------------------------------------
BRONZE = [
    ("kardia_bronze.bronze_claims",     "ClaimID"),
    ("kardia_bronze.bronze_feedback",   "feedback_id"),
    ("kardia_bronze.bronze_providers",  "ProviderID"),
    ("kardia_bronze.bronze_encounters", "ID"),
    ("kardia_bronze.bronze_patients",   "ID"),
]

# -------------------------------------------------------------------------
# Silver-layer test contract: required column sets per table
# -------------------------------------------------------------------------
SILVER_CONTRACTS = {
    "kardia_silver.silver_claims": {
        "claim_id", "patient_id", "provider_id", "claim_amount",
        "claim_date", "diagnosis_code", "procedure_code",
        "claim_status", "claim_type", "claim_submission_method", "_ingest_ts"
    },
    "kardia_silver.silver_patients": {
        "id", "birth_year", "marital", "race", "ethnicity", "gender"
    },
    "kardia_silver.silver_encounters": {
        "encounter_id", "patient_id", "START_TS", "CODE", "DESCRIPTION",
        "REASONCODE", "REASONDESCRIPTION"
    },
}

# -------------------------------------------------------------------------
# Gold-layer test contract: columns that must not contain nulls
# -------------------------------------------------------------------------
GOLD_NOT_NULL = {
    "kardia_gold.gold_patient_lifecycle": ["patient_id"],
    "kardia_gold.gold_feedback_satisfaction": ["provider_id", "avg_score"],
}

# -------------------------------------------------------------------------
# Downstream duplicate suppression map:
# If a Bronze table has duplicates, but the related Silver table does not,
# treat the test as a PASS.
# -------------------------------------------------------------------------
SUPPRESS = {
    "kardia_bronze.bronze_patients": ("kardia_silver.silver_patients", "id")
}
