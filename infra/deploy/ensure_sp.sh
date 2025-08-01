#!/usr/bin/env bash
# ensure_sp.sh
# Ensure a working Azure service principal (SP) with access to ADLS Gen2
# and sync its credentials into a Databricks secret scope.
#
# USAGE:
#   bash infra/deploy/ensure_sp.sh           # Create SP if missing (no rotation)
#   bash infra/deploy/ensure_sp.sh --rotate  # Rotate secret and update Databricks

set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"

# Load environment variables
source "$here/../.env"

# Required values from .env
: "${SUB:?SUB missing in .env}"    # Azure subscription ID
: "${RG:?RG  missing in .env}"     # Resource group name
: "${ADLS:?ADLS missing in .env}"  # ADLS Gen2 storage account name

# Databricks secret scope name (default = 'kardia')
SCOPE="${SCOPE:-kardia}"
YEARS="${YEARS:-1}"       # Secret expiration duration (default = 1 year)

# Resource ID for RBAC assignment
STG_SCOPE="/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$ADLS"

# Should we rotate the secret?
ROTATE=0
if [[ "${1:-}" == "--rotate" ]]; then ROTATE=1; fi

# Authenticate Azure CLI to correct subscription
az account set --subscription "$SUB" >/dev/null

# Ensure Databricks CLI is installed and configured
if ! command -v databricks >/dev/null 2>&1; then
  echo "ERROR: Databricks CLI not found in PATH." >&2
  exit 1
fi
: "${DATABRICKS_HOST:?DATABRICKS_HOST missing; run 'source infra/deploy/auth.sh'}"
: "${DATABRICKS_TOKEN:?DATABRICKS_TOKEN missing; run 'source infra/deploy/auth.sh'}"

APP_NAME="kardiaflow-sp"

# Lookup service principal by display name
CLIENT_ID="$(az ad sp list --display-name "$APP_NAME" --query "[0].appId" -o tsv 2>/dev/null || true)"
TENANT_ID="$(az account show --query tenantId -o tsv)"

if [[ -z "$CLIENT_ID" ]]; then
  echo "Creating service principal '$APP_NAME' and assigning RBAC on $ADLS ..."

  # Create SP + assign storage contributor role; returns a new secret
  read -r CLIENT_ID CLIENT_SECRET TENANT_ID <<<"$(az ad sp create-for-rbac \
      --name  "$APP_NAME" \
      --role  "Storage Blob Data Contributor" \
      --scopes "$STG_SCOPE" \
      --query '[appId, password, tenant]' -o tsv | tr -d '\r')"

  if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" || -z "$TENANT_ID" ]]; then
    echo "ERROR: Failed to create service principal." >&2; exit 1
  fi
  echo "SP created (appId=$CLIENT_ID)."

  # Ensure the Databricks secret scope exists and sync all credentials into it
  databricks secrets create-scope --scope "$SCOPE" --initial-manage-principal users >/dev/null 2>&1 || true
  CLIENT_SECRET="$CLIENT_SECRET" TENANT_ID="$TENANT_ID" CLIENT_ID="$CLIENT_ID" SCOPE="$SCOPE" \
    bash "$here/sync_dbx_secrets.sh"
  echo "Synced new credentials to Databricks scope '$SCOPE'."

else
  echo "Service principal '$APP_NAME' exists (appId=$CLIENT_ID). Ensuring RBAC on $ADLS ..."

  # Ensure the SP has the required role (safe to re-run)
  az role assignment create \
    --assignee "$CLIENT_ID" \
    --role "Storage Blob Data Contributor" \
    --scope "$STG_SCOPE" >/dev/null 2>&1 || true
  echo "RBAC ensured."

  if [[ "$ROTATE" -eq 1 ]]; then
    echo "Rotating SP secret (valid ${YEARS}y) ..."

    # Generate a new client secret
    CLIENT_SECRET="$(az ad sp credential reset \
        --id "$CLIENT_ID" \
        --years "$YEARS" \
        --query password -o tsv | tr -d '\r')"
    if [[ -z "$CLIENT_SECRET" ]]; then
      echo "ERROR: Secret rotation failed." >&2; exit 1
    fi

    # Sync rotated secret into Databricks scope
    databricks secrets create-scope --scope "$SCOPE" --initial-manage-principal users >/dev/null 2>&1 || true
    CLIENT_SECRET="$CLIENT_SECRET" TENANT_ID="$TENANT_ID" CLIENT_ID="$CLIENT_ID" SCOPE="$SCOPE" \
      bash "$here/sync_dbx_secrets.sh"
    echo "Synced rotated credentials to Databricks scope '$SCOPE'."
  else
    echo "No rotation requested. Existing secret in scope '$SCOPE' will be reused."
  fi
fi

echo
echo "Reference (save if needed):"
echo "  client_id = $CLIENT_ID"
echo "  tenant_id = $TENANT_ID"
[[ -n "${CLIENT_SECRET:-}" ]] && echo "  client_secret = (updated and synced)" || true
