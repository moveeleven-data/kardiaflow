import pandas as pd
import os

# Load original dataset
df = pd.read_csv("data/raw/claims/kaggle_enhanced_health_insurance_claims.csv")

# Extract claims subset
claims_columns = [
    "ClaimID", "PatientID", "ProviderID", "ClaimAmount", "ClaimDate",
    "DiagnosisCode", "ProcedureCode", "ClaimStatus", "ClaimType", "ClaimSubmissionMethod"
]
claims_df = df[claims_columns]

# Extract providers subset (deduplicated)
providers_columns = ["ProviderID", "ProviderSpecialty", "ProviderLocation"]
providers_df = df[providers_columns].drop_duplicates(subset="ProviderID")

# Save to proper files
os.makedirs("data/raw/claims", exist_ok=True)
claims_df.to_csv("data/raw/claims/claims.csv", index=False)
providers_df.to_csv("data/raw/claims/providers.csv", index=False)

print("claims.csv and providers.csv created from enhanced dataset.")
