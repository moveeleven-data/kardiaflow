# kflow/validation/config.py
"""Kardiaflow validations - Configuration.

Defines status constants, output table, run timestamp, table registries
for Bronze/Silver/Gold, and duplicate-suppression rules.
"""

from datetime import datetime

# Constants for test status outcomes
PASS  = "PASS"
FAIL  = "FAIL"
ERROR = "ERROR"

# Output location for all validation results
RESULTS_TABLE = "kardia_validation.smoke_results"

# Timestamp applied to all records in a given run
RUN_TS = datetime.utcnow()

# Bronze: (table_name, primary_key)
BRONZE = [
    ("kardia_bronze.bronze_claims",     "ClaimID"),
    ("kardia_bronze.bronze_feedback",   "feedback_id"),
    ("kardia_bronze.bronze_providers",  "ProviderID"),
    ("kardia_bronze.bronze_encounters", "ID"),
    ("kardia_bronze.bronze_patients",   "ID"),
]

# Silver: expected columns per table (schema contract)
SILVER_CONTRACTS = {
    "kardia_silver.silver_claims": {
        "claim_id",
        "patient_id",
        "provider_id",
        "claim_amount",
        "claim_date",
        "diagnosis_code",
        "procedure_code",
        "claim_status",
        "claim_type",
        "claim_submission_method",
        "_ingest_ts",
    },
    "kardia_silver.silver_patients": {
        "id",
        "birth_year",
        "marital",
        "race",
        "ethnicity",
        "gender",
    },
    "kardia_silver.silver_encounters": {
        "encounter_id",
        "patient_id",
        "START_TS",
        "CODE",
        "DESCRIPTION",
        "REASONCODE",
        "REASONDESCRIPTION",
    },
}

# Gold: columns that must never be NULL
GOLD_NOT_NULL = {
    "kardia_gold.gold_patient_lifecycle": ["patient_id"],
    "kardia_gold.gold_feedback_satisfaction": ["provider_id"],
    "kardia_gold.gold_claim_approval_by_specialty": ["provider_specialty"],
    "kardia_gold.gold_provider_daily_spend": ["provider_id"],
}

# Duplicate suppression map: if Bronze has duplicates, allow PASS if the mapped
# Silver table has no duplicates for the corresponding key.
SUPPRESS = {
    "kardia_bronze.bronze_patients": ("kardia_silver.silver_patients", "id"),
}