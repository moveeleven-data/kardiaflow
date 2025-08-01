# config.py
# Configuration for Kardiaflow smoke tests
#
# - Test status constants and run timestamp
# - Table-level validation contracts for Bronze, Silver, and Gold layers
# - Optional suppression logic for primary key duplication checks
from datetime import datetime

# Constants for test status outcomes
PASS  = "PASS"
FAIL  = "FAIL"
ERROR = "ERROR"

# Global config for this smoke test run
RESULTS_TABLE = "kardia_validation.smoke_results" # Output table for all test results
RUN_TS = datetime.utcnow()  # UTC timestamp for this run (applied to all log records)

# Bronze Layer: List of (table_name, primary_key) tuples
# Used for row count, PK uniqueness, and null PK checks
BRONZE = [
    ("kardia_bronze.bronze_claims",     "ClaimID"),
    ("kardia_bronze.bronze_feedback",   "feedback_id"),
    ("kardia_bronze.bronze_providers",  "ProviderID"),
    ("kardia_bronze.bronze_encounters", "ID"),
    ("kardia_bronze.bronze_patients",   "ID"),
]

# Silver Layer: Expected column sets per table (schema contracts)
# Ensures no expected columns are missing (guards against schema drift)
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

# Gold Layer: Columns that must not contain NULLs (critical for analytics)
# Ensures output completeness and avoids downstream join or metric errors
GOLD_NOT_NULL = {
    "kardia_gold.gold_patient_lifecycle":     ["patient_id"],
    "kardia_gold.gold_feedback_satisfaction": ["provider_id", "avg_score"],
}

# Duplicate Suppression:
# Allow a Bronze table to pass the "duplicate PK" check if the downstream
# Silver table contains no duplicates for the mapped key. Useful in cases
# where upstream duplicates are known but resolved later in the pipeline.
SUPPRESS = {
    "kardia_bronze.bronze_patients": ("kardia_silver.silver_patients", "id")
}
