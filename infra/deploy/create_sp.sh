#!/usr/bin/env bash
# infra/deploy/create_sp.sh
# Make / reuse an SP, grant “Storage Blob Data Contributor” on the lake account,
# and echo the three OAuth values you need for Databricks.

set -euo pipefail

# Load env
here="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=/dev/null
source "$here/../.env"

: "${SUB:?SUB missing in .env}"
: "${RG:?RG  missing in .env}"
: "${ADLS:?ADLS missing in .env}"

APP_NAME="kardiaflow-sp"
SCOPE="/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$ADLS"

# Try to create
read -r CLIENT_ID CLIENT_SECRET TENANT_ID <<<"$(az ad sp create-for-rbac \
  --name  "$APP_NAME" \
  --role  "Storage Blob Data Contributor" \
  --scopes "$SCOPE" \
  --query '[appId, password, tenant]' -o tsv | tr -d '\r')"

# If secret came back empty, the SP already existed – reset creds
if [[ -z "$CLIENT_SECRET" ]]; then
  echo "SP \"$APP_NAME\" already exists – resetting its secret ..."
  CLIENT_SECRET="$(az ad sp credential reset \
      --id     "$CLIENT_ID" \
      --years  1 \
      --query  password -o tsv | tr -d '\r')"
fi

# Get tenant if blank
if [[ -z "$TENANT_ID" || "$TENANT_ID" == "null" ]]; then
  TENANT_ID="$(az account show --query tenantId -o tsv)"
fi

# Final sanity check
if [[ -z "$CLIENT_SECRET" || -z "$TENANT_ID" ]]; then
  echo "ERROR: still missing client_secret or tenant_id. Investigate manually." >&2
  exit 1
fi

# Done
cat <<EOF

Service principal ready — add these to the “kardia” secret scope:

  client_id     = $CLIENT_ID
  client_secret = $CLIENT_SECRET
  tenant_id     = $TENANT_ID

EOF
