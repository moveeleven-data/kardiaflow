#!/usr/bin/env bash
# Generate an account-level SAS for kardiaadlsdemo
# and store it in the Databricks secret scope ‹kardia› under key ‹adls_lake_sas›.

set -euo pipefail

# ───────────── 0. Locate repo & .env ────────────────────────────────────────
here="$(cd "$(dirname "$0")" && pwd)"      # …/infra/deploy
infra_root="$here/.."                      # …/infra
ENV_FILE="$infra_root/.env"

[[ -f "$ENV_FILE" ]] || {
  echo "ERROR: .env not found at $ENV_FILE" >&2; exit 1; }

# shellcheck source=/dev/null
source "$ENV_FILE"
: "${DATABRICKS_PAT:?ERROR: Set DATABRICKS_PAT in infra/.env}"

# 1. Set Azure subscription
az account set --subscription "$SUB"

# 2. Resolve Databricks host & export creds
DB_HOST="$(az deployment group show \
             -g "$RG" --name "$DEPLOY" \
             --query 'properties.outputs.databricksUrl.value' -o tsv)"

export DATABRICKS_HOST="https://${DB_HOST}"
export DATABRICKS_TOKEN="$DATABRICKS_PAT"

# 3. Ensure secret scope exists (idempotent)
databricks secrets create-scope "$SCOPE" \
  --initial-manage-principal users 2>/dev/null || true

# 4. Generate ACCOUNT-level SAS
SAS_EXPIRY="$(date -u -d '+180 days' '+%Y-%m-%dT%H:%MZ' 2>/dev/null || \
              gdate -u -d '+180 days' '+%Y-%m-%dT%H:%MZ')"

ACCOUNT_SAS=$(
  az storage account generate-sas \
    --account-name "$ADLS" \
    --https-only \
    --expiry "$SAS_EXPIRY" \
    --services bf \
    --resource-types sco \
    --permissions acdlrw \
    -o tsv
)
ACCOUNT_SAS="${ACCOUNT_SAS#?}"


# 5. Store / overwrite the secret value
databricks secrets put-secret "$SCOPE" adls_lake_sas \
  --string-value "$ACCOUNT_SAS"

echo "Stored new account-level SAS in scope '$SCOPE'/adls_lake_sas (expires $SAS_EXPIRY UTC)"
