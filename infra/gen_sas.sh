#!/usr/bin/env bash
set -euo pipefail

# ─── CONFIGURATION ────────────────────────────
# edit only these values:
SUB="cfe9f138-14a6-4e91-9a90-04d4d62999f9"
RG="kardia-rg-dev"
DEPLOY="kardiaflow"
ADLS="kardiaadlsdemo"
CONT="raw"
PROFILE="kardia"
# The PAT must come from the environment:
: "${DATABRICKS_PAT:?Environment variable DATABRICKS_PAT must be set}"
PAT="$DATABRICKS_PAT"
# ───────────────────────────────────────────────

# 1) Azure context
az account set --subscription "$SUB"

# 2) Get your workspace URL
DB_HOST=$(az deployment group show \
  -g "$RG" -n "$DEPLOY" \
  --query properties.outputs.databricksUrl.value -o tsv)
export DATABRICKS_HOST="https://${DB_HOST}"
export DATABRICKS_TOKEN="$PAT"
echo "Databricks host: $DATABRICKS_HOST"

# 3) Configure Databricks CLI non‑interactively
databricks configure --token \
  --host  "$DATABRICKS_HOST" \
  --token "$DATABRICKS_TOKEN" \
  --profile "$PROFILE"

# 4) Create the secret scope if needed
databricks secrets create-scope "$PROFILE" \
  --initial-manage-principal users \
  --profile "$PROFILE" 2>/dev/null || true

# 5) Generate a 24 h SAS for your raw container
SAS_EXPIRY=$(date -u -d "+1 day" '+%Y-%m-%dT%H:%MZ')
CONN_STR=$(az storage account show-connection-string \
  --resource-group "$RG" \
  --name "$ADLS" -o tsv)

RAW_SAS=$(az storage container generate-sas \
  --connection-string "$CONN_STR" \
  --name            "$CONT" \
  --permissions     rl \
  --expiry          "$SAS_EXPIRY" \
  --https-only      \
  --output          tsv)

# 6) Store the SAS in Databricks secrets
echo -n "$RAW_SAS" | databricks secrets put-secret \
  "$PROFILE" adls_raw_sas \
  --profile "$PROFILE"

echo "SAS stored in $PROFILE/adls_raw_sas (expires $SAS_EXPIRY UTC)"
