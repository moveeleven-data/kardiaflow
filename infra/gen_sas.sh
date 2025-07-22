#!/usr/bin/env bash
set -euo pipefail

# Load environment variables
source "$(dirname "$0")/.env"

# 1. Ensure all az commands are scoped to the correct Azure account
az account set --subscription "$SUB"

# 2. Get the Databricks workspace URL required for CLI auth
DB_HOST=$(az deployment group show \
  -g "$RG" -n "$DEPLOY" \
  --query properties.outputs.databricksUrl.value -o tsv)
export DATABRICKS_HOST="https://${DB_HOST}"
export DATABRICKS_TOKEN="$PAT"
echo "Databricks host: $DATABRICKS_HOST"

# 3. Configure Databricks CLI non‑interactively
databricks configure --token \
  --host  "$DATABRICKS_HOST" \
  --token "$DATABRICKS_TOKEN" \
  --profile "$PROFILE"

# 4. Create the secret scope. Ensure script doesn't fail if secret already exists.
databricks secrets create-scope "$PROFILE" \
  --initial-manage-principal users \
  --profile "$PROFILE" 2>/dev/null || true

# 5. Generate a 24h SAS token for 'Raw' container
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
  --output          tsv) # TSV used to cleanly extract token string

# 6. Store the SAS in Databricks secrets
echo -n "$RAW_SAS" | databricks secrets put-secret \
  "$PROFILE" adls_raw_sas \
  --profile "$PROFILE"

echo "SAS stored in $PROFILE/adls_raw_sas (expires $SAS_EXPIRY UTC)"
