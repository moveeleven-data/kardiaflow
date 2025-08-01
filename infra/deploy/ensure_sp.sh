#!/usr/bin/env bash
# Ensure a single reusable service principal exists, ensure RBAC on today's storage account,
# and (when --rotate) rotate the secret AND sync values into a Databricks secret scope.
#
# Usage:
#   bash infra/deploy/ensure_sp.sh           # idempotent; no rotation; assumes scope already has the secret
#   bash infra/deploy/ensure_sp.sh --rotate  # rotate secret & auto-sync to Databricks scope (recommended for daily rebuild)
#
# Requires:
#   - az CLI logged into the correct subscription (Step 1)
#   - Databricks CLI authenticated (Step 5) before calling this script
#
# Env (from infra/.env):
#   SUB, RG, ADLS, (optional) SCOPE='kardia', YEARS=1

set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$here/../.env"

: "${SUB:?SUB missing in .env}"
: "${RG:?RG  missing in .env}"
: "${ADLS:?ADLS missing in .env}"
SCOPE="${SCOPE:-kardia}"         # Databricks secret scope name
YEARS="${YEARS:-1}"

# For RBAC assignment to the storage account
STG_SCOPE="/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$ADLS"

ROTATE=0
if [[ "${1:-}" == "--rotate" ]]; then ROTATE=1; fi

# Basic checks
az account set --subscription "$SUB" >/dev/null

if ! command -v databricks >/dev/null 2>&1; then
  echo "ERROR: Databricks CLI not found in PATH." >&2
  exit 1
fi
: "${DATABRICKS_HOST:?DATABRICKS_HOST missing; run 'source infra/deploy/auth.sh'}"
: "${DATABRICKS_TOKEN:?DATABRICKS_TOKEN missing; run 'source infra/deploy/auth.sh'}"

APP_NAME="kardiaflow-sp"

# Find or create SP (first match by display name)
CLIENT_ID="$(az ad sp list --display-name "$APP_NAME" --query "[0].appId" -o tsv 2>/dev/null || true)"
TENANT_ID="$(az account show --query tenantId -o tsv)"

if [[ -z "$CLIENT_ID" ]]; then
  echo "Creating service principal '$APP_NAME' and assigning RBAC on $ADLS ..."
  # create-for-rbac returns a fresh secret
  read -r CLIENT_ID CLIENT_SECRET TENANT_ID <<<"$(az ad sp create-for-rbac \
      --name  "$APP_NAME" \
      --role  "Storage Blob Data Contributor" \
      --scopes "$STG_SCOPE" \
      --query '[appId, password, tenant]' -o tsv | tr -d '\r')"

  if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" || -z "$TENANT_ID" ]]; then
    echo "ERROR: Failed to create service principal." >&2; exit 1
  fi
  echo "SP created (appId=$CLIENT_ID)."

  # Ensure the scope exists, then sync secrets
  databricks secrets create-scope --scope "$SCOPE" --initial-manage-principal users >/dev/null 2>&1 || true
  CLIENT_SECRET="$CLIENT_SECRET" TENANT_ID="$TENANT_ID" CLIENT_ID="$CLIENT_ID" SCOPE="$SCOPE" \
    bash "$here/sync_dbx_secrets.sh"
  echo "Synced new credentials to Databricks scope '$SCOPE'."

else
  echo "Service principal '$APP_NAME' exists (appId=$CLIENT_ID). Ensuring RBAC on $ADLS ..."
  # Idempotent RBAC
  az role assignment create \
    --assignee "$CLIENT_ID" \
    --role "Storage Blob Data Contributor" \
    --scope "$STG_SCOPE" >/dev/null 2>&1 || true
  echo "RBAC ensured."

  if [[ "$ROTATE" -eq 1 ]]; then
    echo "Rotating SP secret (valid ${YEARS}y) ..."
    CLIENT_SECRET="$(az ad sp credential reset \
        --id "$CLIENT_ID" \
        --years "$YEARS" \
        --query password -o tsv | tr -d '\r')"
    if [[ -z "$CLIENT_SECRET" ]]; then
      echo "ERROR: Secret rotation failed." >&2; exit 1
    fi

    # Ensure the scope exists, then sync secrets
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
[[ -n "${CLIENT_SECRET:-}" ]] && echo "  client_secret = (updated & synced)" || true
