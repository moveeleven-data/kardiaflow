#!/usr/bin/env bash
# infra/deploy/ensure_sp.sh
#
# Create or rotate an AAD service principal and grant ADLS RBAC.
# Sync service principal credentials into a Databricks secret scope.

set -euo pipefail


# --- Env and inputs ---

# Script directory (absolute path)
here="$(cd "$(dirname "$0")" && pwd)"

# Load environment variables from .env
# shellcheck disable=SC1091
source "$here/../.env"

# Required variables (fail if missing)
: "${SUB:?SUB missing in .env}"
: "${RG:?RG missing in .env}"
: "${ADLS:?ADLS missing in .env}"
: "${DATABRICKS_HOST:?Run: source infra/.env && source infra/deploy/auth.sh}"
: "${DATABRICKS_TOKEN:?Run: source infra/.env && source infra/deploy/auth.sh}"

# Optional variables with defaults
SCOPE="${SCOPE:-kardia}"
YEARS="${YEARS:-1}"
APP_NAME="${APP_NAME:-kardiaflow-sp}"


# --- Azure context ---

# Set the active subscription
az account set --subscription "$SUB" >/dev/null

# Resource scope for assigning Storage Blob Data Contributor role
STG_SCOPE="/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$ADLS"

# Flag: rotate secret if "--rotate" is passed as first argument
ROTATE=0
[[ "${1:-}" == "--rotate" ]] && ROTATE=1



# --- Lookup existing SP and tenant ---

# Find SP by display name; empty result means "create"
CLIENT_ID="$(az ad sp list \
  --display-name "$APP_NAME" \
  --query '[0].appId' -o tsv 2>/dev/null || true)"

# Always capture current tenant ID
TENANT_ID="$(az account show --query tenantId -o tsv)"


# --- Create path ---

if [[ -z "$CLIENT_ID" ]]; then
  echo "Creating service principal '$APP_NAME' and assigning RBAC on $ADLS ..."

  # Create a new SP with Storage Blob Data Contributor role on ADLS
  read -r CLIENT_ID CLIENT_SECRET TENANT_ID <<<"$(az ad sp create-for-rbac \
      --only-show-errors \
      --name   "$APP_NAME" \
      --role   'Storage Blob Data Contributor' \
      --scopes "$STG_SCOPE" \
      --query  '[appId, password, tenant]' -o tsv | tr -d '\r')"

  # Ensure all values were returned, otherwise fail
  [[ -n "$CLIENT_ID" && -n "$CLIENT_SECRET" && -n "$TENANT_ID" ]] \
    || { echo "ERROR: SP creation failed."; exit 1; }

  echo "SP created (appId=$CLIENT_ID)."

  # Sync new SP credentials into Databricks secret scope
  SCOPE="$SCOPE" TENANT_ID="$TENANT_ID" CLIENT_ID="$CLIENT_ID" CLIENT_SECRET="$CLIENT_SECRET" \
    bash "$here/sync_dbx_secrets.sh"


# --- Existing path ---

else
  echo "Ensuring RBAC on $ADLS for '$APP_NAME' ..."

  # Grant Storage Blob Data Contributor role if missing
  az role assignment create --only-show-errors \
    --assignee "$CLIENT_ID" \
    --role    "Storage Blob Data Contributor" \
    --scope   "$STG_SCOPE" >/dev/null 2>&1 || true

  echo "RBAC ensured."

  if [[ "$ROTATE" -eq 1 ]]; then
    echo "Rotating SP secret (${YEARS}y) and syncing to scope '$SCOPE' ..."

    # Rotate secret and capture new client_secret
    CLIENT_SECRET="$(az ad sp credential reset --only-show-errors \
        --id "$CLIENT_ID" \
        --years "$YEARS" \
        --query password -o tsv | tr -d '\r')"

    # Abort if rotation fails
    [[ -n "$CLIENT_SECRET" ]] \
      || { echo "ERROR: Secret rotation failed."; exit 1; }

    # Sync rotated secret into Databricks scope
    SCOPE="$SCOPE" TENANT_ID="$TENANT_ID" CLIENT_ID="$CLIENT_ID" CLIENT_SECRET="$CLIENT_SECRET" \
      bash "$here/sync_dbx_secrets.sh"

  else
    # Just refresh IDs in the scope (no new secret generated)
    if databricks secrets list-scopes -o json | grep -q "\"name\": *\"$SCOPE\""; then
      databricks secrets put-secret "$SCOPE" sp_tenant_id --string-value "$TENANT_ID" >/dev/null 2>&1 || true
      databricks secrets put-secret "$SCOPE" sp_client_id  --string-value "$CLIENT_ID"  >/dev/null 2>&1 || true
    fi

    echo "No rotation requested."
  fi
fi


echo "Done."